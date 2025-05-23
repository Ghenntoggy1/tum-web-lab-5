# Laboratory Work 5 - Websockets
## Student: Gusev Roman
## Group: FAF-222

### Requirements:
1. Write a CLI Program.
2. The program should implement at least the following CLI:
```
go2web -u <URL>         # make an HTTP request to the specified URL and print the response
go2web -s <search-term> # make an HTTP request to search the term using your favorite search engine and print top 10 results
go2web -h               # show this help
```
3. The responses from request should be human-readable (e.g. no HTML tags in the output)
4. Any programming language can be used, but not the built-in/third-party libraries for making HTTP requests. GUI applications aren't allowed. The app has to be launched with go2web executable.

### Functionalities:
#### Main functionalities:
1. `go2web -h` or `go2web --help` - display help menu.
2. `go2web -c` or `go2web --clear` - clear local file cache.
3. `go2web -s "<search_term>"` or `go2web --search "<search_term>"` - search a phrase or a single word using one of the 2 possible options for the search engine.
4. `go2web -u "url"` or `go2web --url "url"` - open the contents of the url, either JSON or HTML contents displayed in the CLI.

#### Additional functionalities:
1. Implemented In-File Cache mechanism, that stores `url-data` pairs, in JSON format.
2. Implemented handling for Redirection Responses.
3. Implemented Accessing mechanism for links from search engine in CLI (based on user choice).
4. Implemented Content Negotiation (based on Content-Type header from response and Accept).

### How to run:
#### Prerequisites:
1. Python (version >= 1.13.2, may work on older, but not sure).
#### Using .exe:
1. For a better structure, create a folder and place the executable [(go2web.exe)](https://github.com/Ghenntoggy1/tum-web-lab-5/releases) there.
2. Create `.venv` virtual environment using `python3 -m venv /path/to/thisFolder/` and import `requirements.txt` in the same folder.
3. Install libraries using `pip install -r /path/to/thisFolder/requirements.txt`.
4. Create `.env` file. Structure:
```
GOOGLE_API_KEY="<GOOGLE_PROGRAMMABLE_SEARCH_ENGINE_API_KEY>"
CX="<GOOGLE_PROGRAMMABLE_SEARCH_ENGINGE_ID>"
SERPAPI_API_KEY="<SERPAPI_API_KEY>"
ENGINE="duckduckgo"
REGION="wt-wt"
MAX_REDIRECTS=5
```
5. Run `go2web.exe`.

#### Using code:
1. Pull this repo.
2. Open preferred IDE.
3. Create `.venv` virtual environment using `python3 -m venv /path/to/thisFolder/` and import `requirements.txt` in the same folder.
4. Install libraries using `pip install -r /path/to/thisFolder/requirements.txt`.
5. Create `.env` file. Structure:
```
GOOGLE_API_KEY="<GOOGLE_PROGRAMMABLE_SEARCH_ENGINE_API_KEY>"
CX="<GOOGLE_PROGRAMMABLE_SEARCH_ENGINGE_ID>"
SERPAPI_API_KEY="<SERPAPI_API_KEY>"
ENGINE="duckduckgo"
REGION="wt-wt"
MAX_REDIRECTS=5
```
6. Open CLI.
7. Run this command: `pyinstaller --onefile .\go2web.py`.
8. Go to `dist` folder.
9. Run `go2web.exe`.

### Demo:
![demo_gif](/README_files/video_functionality.gif)