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

def fetch_url(url: str, data_type: str) -> dict:
    # Check if the response is already in the cache
    cached_response = cache.get(url)
    if cached_response:
        print("Cache hit!")
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
        f"Accept: {data_type}\r\n"
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
    data = response.decode('utf-8', errors='ignore')
    headers, body = data.split('\r\n\r\n', 1)
    json_body = re.search(r'\{.*\}', body, re.DOTALL).group(0)
    mapping = dict.fromkeys(range(32))
    clean_json_body = json_body.translate(mapping)
    # clean_json_body = clean_json_body.replace("118d", "")  # Hardcoded value removal since I could not solve the issue, response comes chunked and my
    #                                                        # methods were not able to take the entire response
    response_data = json.loads(clean_json_body)
    print(f"Response:\n{response_data}")

    # Store the response in the cache
    cache.set(url, response_data)

    return response_data

def search(search_term: list[str]) -> str:
    api_key = getenv('SERPAPI_API_KEY')
    cx = getenv('CX')
    engine = getenv('ENGINE')
    region = getenv('REGION')
    search_term_query = '+'.join(search_term[0].split())
    url = f"https://serpapi.com/search?engine={engine}&kl={region}&q={search_term_query}&api_key={api_key}"
    # url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q={search_term_query}&num=10"
    print(f"Search URL: {url}")
    search_results = fetch_url(url, "application/json")
    search_items = search_results.get('organic_results')
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
    print(f"Arguments provided: {args}")
    if args.url:
        # TODO: Implement HTTP Request and HTML Parsing
        print(f"NOT IMPLEMENTED!")
    elif args.search:
        # TODO: Implement search for top 10 results using search engine based on the search term
        print(f"WIP!")
        search(args.search)
    elif args.clear:
        # Clear the cache
        cache.clear()
        print("Cache cleared!")
    else:
        print(help_message)

if __name__ == '__main__':
    main()