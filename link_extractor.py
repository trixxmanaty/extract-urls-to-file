#!/usr/bin/env python3
"""
Single-page link extractor.

- Fetches a page with robust error handling and retries
- Parses all <a href="..."> links (absolute + relative)
- Normalizes to absolute URLs, removes fragments (#...)
- Writes unique links to a file or stdout

Usage:
    python link_extractor.py https://example.com -o links.txt --timeout 10 --sort
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Set
from urllib.parse import urljoin, urldefrag, urlparse

import requests
from bs4 import BeautifulSoup

# Retry is available through urllib3 (dep of requests). If import fails, we just skip retries.
try:
    from urllib3.util.retry import Retry  # type: ignore
    HAVE_RETRY = True
except Exception:  # pragma: no cover
    HAVE_RETRY = False


DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def build_session(user_agent: str, timeout: float) -> requests.Session:
    """
    Create a configured Session with headers and (if available) retries.
    """
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": user_agent or DEFAULT_UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en,en-US;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
    )

    if HAVE_RETRY:
        # Backoff & retry transient errors
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset({"HEAD", "GET", "OPTIONS"}),
            raise_on_status=False,
        )
        from requests.adapters import HTTPAdapter

        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

    # Attach default timeout to session via wrapper
    # We'll use this in fetch_html for each request.
    session._default_timeout = timeout  # type: ignore[attr-defined]
    return session


def fetch_html(session: requests.Session, url: str) -> str:
    """
    GET the URL and return HTML text. Raises ValueError on non-HTML responses.
    """
    timeout = getattr(session, "_default_timeout", 10.0)  # type: ignore[attr-defined]
    try:
        resp = session.get(url, timeout=timeout)
        # Raise HTTP errors (4xx/5xx)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Request failed for {url}: {exc}") from exc

    ctype = resp.headers.get("Content-Type", "")
    if "text/html" not in ctype.lower():
        raise ValueError(f"Unsupported content type for {url}: {ctype or 'unknown'}")

    # requests handles encoding; fallback to apparent if not provided
    if not resp.encoding:
        resp.encoding = resp.apparent_encoding  # type: ignore[assignment]

    return resp.text


def extract_base_href(soup: BeautifulSoup, page_url: str) -> str:
    """
    Determine the base URL for resolving relative links.
    Honors <base href="..."> when present; otherwise uses page_url.
    """
    base_tag = soup.find("base", href=True)
    if base_tag and base_tag["href"]:
        return urljoin(page_url, str(base_tag["href"]))
    return page_url


def is_web_link(href: str) -> bool:
    """
    Filter out non-http(s) schemes and empty/fragment-only links.
    """
    if not href:
        return False
    href = href.strip()
    if href.startswith("#"):
        return False
    parsed = urlparse(href)
    if parsed.scheme in ("http", "https", ""):
        return True
    return False  # mailto:, javascript:, tel:, data:, etc.


def normalize_url(href: str, base_url: str) -> str:
    """
    Resolve to absolute URL and strip fragments.
    """
    absolute = urljoin(base_url, href)
    absolute, _fragment = urldefrag(absolute)
    return absolute


def extract_links(html: str, page_url: str) -> Set[str]:
    """
    Parse HTML and return a set of absolute, fragment-free http(s) URLs.
    """
    soup = BeautifulSoup(html, "html.parser")
    base_url = extract_base_href(soup, page_url)

    links: Set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not is_web_link(href):
            continue
        absolute = normalize_url(href, base_url)
        # Keep only http(s) after resolution
        if urlparse(absolute).scheme in ("http", "https"):
            links.add(absolute)
    return links


def write_links(links: Iterable[str], output: Path | None) -> None:
    """
    Write links to file (one per line) or stdout if output is None.
    """
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as f:
            for link in links:
                f.write(link + "\n")
    else:
        for link in links:
            print(link)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract unique links from a web page."
    )
    parser.add_argument(
        "url",
        help="The page URL to scrape (e.g., https://example.com).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Path to write links (default: print to stdout).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Request timeout in seconds (default: 10).",
    )
    parser.add_argument(
        "--user-agent",
        default=DEFAULT_UA,
        help="Custom User-Agent string.",
    )
    parser.add_argument(
        "--sort",
        action="store_true",
        help="Sort links alphabetically before output.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # Basic URL sanity check
    parsed = urlparse(args.url)
    if parsed.scheme not in ("http", "https"):
        print("Error: URL must start with http:// or https://", file=sys.stderr)
        return 2

    session = build_session(args.user_agent, args.timeout)

    try:
        html = fetch_html(session, args.url)
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    links = extract_links(html, args.url)
    if args.sort:
        links_out: Iterable[str] = sorted(links)
    else:
        links_out = links

    try:
        write_links(links_out, args.output)
    except OSError as e:
        print(f"Error writing output: {e}", file=sys.stderr)
        return 1

    where = str(args.output) if args.output else "stdout"
    print(f"✓ Extracted {len(links)} links → {where}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
