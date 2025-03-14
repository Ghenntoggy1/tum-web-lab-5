from argparse import HelpFormatter, ArgumentParser
from sys import argv
from dotenv import load_dotenv
from os import getenv

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
        print(f"NOT IMPLEMENTED!")
    else:
        print(help_message)

if __name__ == '__main__':
    main()