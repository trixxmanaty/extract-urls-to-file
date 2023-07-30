# Webpage Link Extractor

This project contains a Python script to extract all unique absolute URLs from a webpage and write them into a text file. This can be useful for indexing purposes.

## Prerequisites

You need Python 3 and the following Python packages: `beautifulsoup4` and `requests`.

You can install these packages using pip:

```bash
pip install beautifulsoup4 requests

## Usage
1. Open the Python file link_extractor.py in a text editor.
2. Modify the following line with your desired URL from which you want to extract links:
```
url = 'https://www.example.com/mypage'

3. If you want to specify a different output file, modify this line:
```
filename = '/path/to/your/output/file.txt'

4. Save the file and run it with Python 3:
```
python link_extractor.py

5. The output file will contain all the unique URLs found on the specified webpage, each URL will be on a new line.

## Notes
Please be aware of the limitations and terms of use of the website you are scraping to ensure your actions are legal and ethical. This code extracts all URLs from the page. Depending on the structure of the site and how it builds URLs, you may need to adapt this script to filter and process URLs to get the ones you need.
