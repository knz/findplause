# Slack reaction finder

A simple UI to search Slack messages that have obtained a specific reaction.

Usage instructions:

1. download the file `findplause.py`
2. ensure python3 is installed
3. install [slackclient](https://pypi.org/project/slackclient/) (e.g. `pip3 install slackclient`)
4. run tool: `python3 findplause.py`  (if need custom port: `python3 findplause.py 12345`)
5. open browser with URL provided by program
6. obtain Slack token with permissions **users:read**, **search:read** and **reactions:read**
7. enter lack token and search dates
8. submit with "search" button
