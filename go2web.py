from argparse import HelpFormatter, ArgumentParser
import json
import re
import socket
from sys import argv
from urllib.parse import urlparse
from dotenv import load_dotenv
from os import getenv
import ssl

load_dotenv()

help_message: str = """HELP:
go2web -u <URL>           # make an HTTP request to the specified URL and print the response
go2web -s "<search-term>" # make an HTTP request to search the term using your favorite search engine and print top 10 results
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
    parser.add_argument('-h', '--help', action='help')

def fetch_url(url) -> dict:
    parsed_url = urlparse(url)
    host = parsed_url.hostname
    port = parsed_url.port if parsed_url.port else 443  # Use port 443 for HTTPS (TLS)
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
    data = response.decode('utf-8', errors='ignore')
    headers, body = data.split('\r\n\r\n', 1)
    json_body = re.search(r'\{.*\}', body, re.DOTALL).group(0)
    mapping =  dict.fromkeys(range(32))
    clean_json_body = json_body.translate(mapping)
    clean_json_body = clean_json_body.replace("118d", "")
    return json.loads(clean_json_body)

def search(search_term: list[str]) -> str:
    api_key = getenv('API_KEY')
    cx = getenv('CX')
    search_term_query = '+'.join(search_term)
    url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q={search_term_query}"

    search_results = fetch_url(url)
    print(json.dumps(search_results, indent=2))

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
    else:
        print(help_message)

if __name__ == '__main__':
    main()