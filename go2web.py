from argparse import HelpFormatter, ArgumentParser
import json
import re
import socket
from sys import argv
from urllib.parse import urlparse
from dotenv import load_dotenv
from os import getenv, path
import ssl
import webbrowser
from typing import Any, Dict, Optional
from enum import Enum
from bs4 import BeautifulSoup, Comment

load_dotenv()

help_message: str = """HELP:
go2web -u <URL>           # make an HTTP request to the specified URL and print the response
go2web -s "<search-term>" # make an HTTP request to search the term using your favorite search engine and print top 10 results
go2web -c                 # clear the cache
go2web -h                 # show this help"""

class CustomFormatter(HelpFormatter):
    def format_help(self):
        help_text = help_message
        return help_text

parser = ArgumentParser(prog='go2web',
                                 description='A Minimalistic Web Browser',
                                 add_help=False,
                                 formatter_class=CustomFormatter)

def add_arguments():
    parser.add_argument('-u', '--url', type=str, metavar = "str")
    parser.add_argument('-s', '--search', type=str, metavar = "str", nargs='+')
    parser.add_argument('-c', '--clear', action='store_true')
    parser.add_argument('-h', '--help', action='help')

class EngineEnum(Enum):
    GOOGLE = 1
    DUCKDUCKGO = 2

class FileCache:
    def __init__(self, cache_file: str = 'cache.json'):
        self.cache_file = cache_file
        # If cachke.json file is not present, then create it and 
        if not path.exists(self.cache_file):
            with open(self.cache_file, 'w') as f:
                # Create an empty JSON object inside cache.json ({})
                f.write('{}')

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        # Read the cache data from the file cache.json
        with open(self.cache_file, 'r') as f:
            cache = json.load(f)
        # find in the cache dict the searched key (url) and return the value (search results)
        return cache.get(key)

    def set(self, key: str, value: Dict[str, Any]) -> None:
        # Read old cache data from the file
        with open(self.cache_file, 'r') as f:
            cache = json.load(f)
        # Add to the cache dict new search results
        cache[key] = value
        with open(self.cache_file, 'w') as f:
            # write the cache back to the file cache.json (if cache was not empty, it will update the cache with new data)
            json.dump(cache, f, indent=4) 

    def clear(self) -> None:
        # Clear the cache by overwriting the cache.json contents with an {}
        with open(self.cache_file, 'w') as f:
            f.write('{}')

# Initialize the cache
cache = FileCache(cache_file='cache.json')

def display_html(body: str) -> None:
    soup = BeautifulSoup(body, 'html.parser')

    # Remove unwanted tags
    for tag in soup(['img', 'script', 'style', 'svg']):
        tag.decompose()

    # Format links
    for a in soup.find_all('a'):
        if a.get('href') == a.text:
            a.replace_with(a.text)
        else:
            a.replace_with(f"{a.text} (link: {a.get('href')})")

    # Format headings
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        heading.replace_with(f"\n{heading.text.upper()}\n")

    # Format paragraphs
    for p in soup.find_all('p'):
        p.replace_with(f"\n{p.text}\n")

    # Format unordered lists
    for ul in soup.find_all('ul'):
        ul.replace_with('\n'.join(f"~ {re.sub(r'\n+', ' ', li.text.rstrip().strip())}" for li in ul.find_all('li')) + '\n')

    # Format ordered lists
    for ol in soup.find_all('ol'):
        ol.replace_with('\n'.join(f"{i + 1}. {re.sub(r'\n+', ' ', li.text.rstrip().strip())}" for i, li in enumerate(ol.find_all('li')))) + '\n'

    # Get the final text
    text = soup.get_text().rstrip().strip()

    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    return text

def handle_chunked_body(chunked_body):
    body = b""
    while True:
        # Find the end of the chunk size line
        chunk_size_end = chunked_body.find(b"\r\n")
        if chunk_size_end == -1:
            break

        # Extract the chunk size (hexadecimal)
        chunk_size_line = chunked_body[:chunk_size_end]
        chunk_size = int(chunk_size_line, 16)

        # If chunk size is 0, we've reached the end
        if chunk_size == 0:
            break

        # Extract the chunk data
        chunk_start = chunk_size_end + 2
        chunk_end = chunk_start + chunk_size
        chunk_data = chunked_body[chunk_start:chunk_end]

        # Append the chunk data to the body
        body += chunk_data

        # Move to the next chunk
        chunked_body = chunked_body[chunk_end + 2:]

    return body


def fetch_url(url: str, max_redirects: int = int(getenv('MAX_REDIRECTS'))) -> dict | str:
    # Check if the response is already in the cache
    cached_response = cache.get(url)
    if cached_response:
        print("\nFound in cache!\n")
        return cached_response

    parsed_url = urlparse(url)
    host = parsed_url.hostname
    port = parsed_url.port if parsed_url.port else 443  # Use port 443 for HTTPS (TLS) since google API uses HTTPS
    path = parsed_url.path if parsed_url.path else "/"
    print(f"Host: {host}, Port: {port}, Path: {path}")
    path = parsed_url.path + "?" + parsed_url.query if parsed_url.query else parsed_url.path
    print(f"Path: {path}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    context = ssl.create_default_context()
    wrapped_sock = context.wrap_socket(sock, server_hostname=host)
    wrapped_sock.connect((host, port))

    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "User-Agent: go2web/1.0\r\n"
        "Connection: close\r\n\r\n"
    )
    print(f"Request:\n{request}")
    wrapped_sock.send(request.encode())

    response = b""
    while True:
        part = wrapped_sock.recv(4096)
        if not part:
            break
        response += part
    wrapped_sock.close()

    # Split the response into headers and body
    header_end = response.find(b"\r\n\r\n")
    headers = response[:header_end].decode("utf-8")
    body = response[header_end + 4:]

    status_line = headers.split("\r\n")[0]
    status_code = int(status_line.split(" ")[1])
    if status_code in (301, 302, 303, 307, 308):
        if max_redirects == 0:
            print("Max redirects reached!")
            return None
        print(f"Redirect detected! Status code: {status_code}")
        # Extract the Location header
        location_header = None
        if 'Location' in headers:
            location_header = re.search(r"Location: (.+)\r\n", headers, re.IGNORECASE)
        elif 'location' in headers:
            location_header = re.search(r"location: (.+)\r\n", headers, re.IGNORECASE)
        
        if location_header:
            new_url = location_header.group(1).strip()
            if not new_url.startswith('http'):
                new_url = f"https://{host}{new_url}"
            
            print(f"Redirecting to: {new_url}")
            return fetch_url(new_url, max_redirects - 1)
        else:
            print("No location header found in the response!")
            return None
    print(headers)
    # Handle chunked encoding
    if "Transfer-Encoding: chunked" in headers or "transfer-encoding: chunked" in headers:
        body = handle_chunked_body(body)
    # check header for content type
    content_type = None
    if 'Content-Type' in headers:
        content_type = re.search(r"Content-Type: (.+)", headers)
    elif 'content-type' in headers:
        content_type = re.search(r"content-type: (.+)", headers)
    charset = None
    data_type = None
    if content_type:
        data_type = content_type.group(1).split(";")[0].strip()
        if "charset" in content_type.group(1):
            charset = re.search(r"charset=(.+)", content_type.group(1)).group(1).strip()
    else:
        print("No content type found in the response header!")
        return None
    
    decoded_body = body.decode(charset) if charset else body.decode('utf-8')
    
    print(f"Data type: {data_type}")
    if "application/json" in data_type:
        json_body = re.search(r'\{.*\}', decoded_body, re.DOTALL).group(0)
        mapping = dict.fromkeys(range(32))
        clean_json_body = json_body.translate(mapping)
        # clean_json_body = clean_json_body.replace("118d", "")  # Hardcoded value removal since I could not solve the issue, response comes chunked and my
        #                                                        # methods were not able to take the entire response. SOLVED: in loop decode response until no more data.
        response_data = json.loads(clean_json_body)
        
        # Store the response in the cache
        cache.set(url, response_data)

        return response_data
    elif "text/html" in data_type:
        pretty_html = display_html(decoded_body)
        cache.set(url, pretty_html)
        return pretty_html
    else:
        print("Invalid data type provided!")
        return None

def search(search_term: list[str], engineEnum: EngineEnum = EngineEnum.DUCKDUCKGO) -> str:
    search_term_query = '+'.join(search_term[0].split())
    if engineEnum == EngineEnum.DUCKDUCKGO:
        api_key = getenv('SERPAPI_API_KEY')
        engine = getenv('ENGINE')
        region = getenv('REGION')
        url = f"https://serpapi.com/search?engine={engine}&kl={region}&q={search_term_query}&api_key={api_key}" # SERP API for DuckDuckGo
    elif engineEnum == EngineEnum.GOOGLE:
        api_key = getenv('GOOGLE_API_KEY')
        cx = getenv('CX')
        url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q={search_term_query}&num=10"
    else:
        print("Invalid search engine provided!")
        return

    print(f"Search URL: {url}")
    search_results = fetch_url(url)
    if not search_results:
        print("No search results found!")
        return
    
    search_items = search_results.get('organic_results' if engineEnum == EngineEnum.DUCKDUCKGO else 'items')
    if search_items:
        for i, item in enumerate(search_items):
            title = item.get('title')
            link = item.get('link')
            snippet = item.get('snippet')
            print(f"{i + 1}. {title}\n{link}\n{snippet}\n")
    else:
        print("No search results found!")

    if search_items:
        print("Select a link to open in the browser or 'q' to exit:")
        choice = input()
        if choice.isdigit() and int(choice) in range(1, 11):
            choice = int(choice)
            print(f"Opening link: {search_items[choice - 1].get('link')}")
            webbrowser.open(search_items[choice - 1].get('link'))
        elif choice.lower() == 'q':
            return
        else:
            print("Invalid choice!")
    

def main():
    add_arguments()
    args = parser.parse_args()
    if not len(argv) > 1:
        print("No arguments provided. Check the help message below:\n")
        print(help_message)
        return

    if args.url:
        output = fetch_url(args.url)
        if type(output) == dict:
            print(json.dumps(output, indent=4))
        elif type(output) == str:
            print(output)
        else:
            print("Invalid data type!")
    elif args.search:
        print(f"Select a search engine to use:\n1. DuckDuckGo\n2. Google")
        choice = input()
        if choice == '1':
            search(args.search, EngineEnum.DUCKDUCKGO)
        elif choice == '2':
            search(args.search, EngineEnum.GOOGLE)
        else:
            print("Invalid choice!")
    elif args.clear:
        # Clear the cache
        cache.clear()
        print("Cache cleared!")
    else:
        print(help_message)

if __name__ == '__main__':
    main()