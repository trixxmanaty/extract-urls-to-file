import requests
from bs4 import BeautifulSoup

def get_links(url):
    # Send a GET request to the URL
    response = requests.get(url)
    # If the GET request is successful, the status code will be 200
    if response.status_code == 200:
        # Get the content of the response
        page_content = response.content
        # Create a BeautifulSoup object and specify the parser
        soup = BeautifulSoup(page_content, 'html.parser')
        # Find all the anchor tags in the HTML
        # Extract the href attribute and add it to a set (to avoid duplicates)
        links = set()
        for anchor in soup.find_all('a'):
            link = anchor.get('href')
            # Skip tags where href attribute is not present or does not start with 'http'
            if link is not None and link.startswith('http'):
                links.add(link)
        # Return the set of links
        return links

def write_to_file(links, filename):
    # Open the file in write mode
    with open(filename, 'w') as f:
        # Write each link on a separate line
        for link in links:
            f.write(link + "\n")

def main():
    url = 'https://www.example.com/mypage'
    # Provide an absolute path where you want to store the file
    filename = '/path/to/your/output/file.txt'
    links = get_links(url)
    write_to_file(links, filename)
    print(f"Extracted {len(links)} links and wrote them to {filename}")

if __name__ == "__main__":
    main()
