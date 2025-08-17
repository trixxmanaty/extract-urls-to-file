# Webpage Link Extractor

A small, typed Python CLI that extracts **unique, absolute http(s) links** from a single webpage and writes them to a file or stdout. It handles relative URLs, honors `<base href>`, removes fragments (`#...`), filters non-web schemes, and includes robust request handling (timeouts, retries, custom User-Agent).

## Features

* Converts **relative → absolute** URLs (`urljoin`), respects `<base href>`
* Filters out `mailto:`, `javascript:`, `tel:`, `data:` links
* **Deduplicates** and optionally `--sort`s output
* **Retries** transient HTTP errors (429/5xx) and uses a reusable `requests.Session`
* Verifies **HTML content-type** before parsing
* CLI flags for output path, timeout, and User-Agent
* Clear exit codes and helpful error messages

## Prerequisites

* **Python 3.10+**
* Packages: `requests`, `beautifulsoup4`
  Install:

```bash
pip install -U requests beautifulsoup4
```

> Tip: Use a virtual environment (`python -m venv .venv && source .venv/bin/activate` on macOS/Linux, or `.venv\Scripts\Activate.ps1` on Windows).

## Usage

Assuming the file is named `link_extractor.py` (replace with your filename if different):

```bash
# Print links to stdout
python link_extractor.py https://example.com

# Save to a file
python link_extractor.py https://example.com -o links.txt

# Sort output alphabetically
python link_extractor.py https://example.com -o links.txt --sort

# Increase/adjust timeout (seconds)
python link_extractor.py https://example.com --timeout 15

# Use a custom User-Agent (may help avoid 403s)
python link_extractor.py https://example.com --user-agent "MyCrawler/1.0 (+contact@example.com)"
```

### Command-line options

```
positional arguments:
  url                     The page URL to scrape (e.g., https://example.com)

optional arguments:
  -o, --output PATH       Write links to file (default: stdout)
  --timeout SECONDS       Request timeout (default: 10)
  --user-agent STRING     Custom User-Agent header
  --sort                  Sort links before output
```

### Output

* One URL per line
* Only `http`/`https` links
* **Fragments removed** (e.g., `https://site/page#section` → `https://site/page`)
* **Unique** links (set semantics)

### Exit codes

* `0` – Success
* `1` – Runtime error (network/HTTP, non-HTML content, write failure)
* `2` – Invalid input (e.g., URL doesn’t start with `http://` or `https://`)

## Examples

```bash
# Extract and pipe to grep
python link_extractor.py https://example.com | grep "/blog/"

# Save, sort, and then count
python link_extractor.py https://example.com -o links.txt --sort && wc -l links.txt
```

## Notes & Etiquette

* **Be polite**: respect the site’s terms of use, `robots.txt`, and rate limits.
* This tool processes **a single page**. It does not crawl multiple pages.
* Some sites build links dynamically with JavaScript; this script parses server-returned HTML only.
* If you encounter `403 Forbidden` or similar, try a realistic `--user-agent`. Some sites block unknown clients.
* If the server responds with non-HTML content, the script will exit with an error indicating the `Content-Type`.

## Troubleshooting

* **403/429 errors**: set a custom `--user-agent`; try again later (server throttling); ensure you’re allowed to fetch the page.
* **Timeouts**: raise `--timeout` or check your network connection.
* **SSL/Certificates**: ensure your system certificates are up to date; avoid disabling verification.
* **Empty output**: page may not contain anchor tags with usable `href` values, or links may be built via client-side JS.

## Roadmap (optional enhancements)

* `--same-domain-only` filtering
* JSON/CSV output formats
* Simple crawler mode with politeness (robots, delay, concurrency limits)

---

**License**: MIT
