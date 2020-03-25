# remapy

Work in progress.

# Features
[ ] GUI <br />
[x] Authentication <br />
[ ] Settings (Path to templates, sync folder, ) <br />
[x] List all folders and files <br />
[ ] Upload file <br />
[ ] Upload via CUPS printer <br />
[x] Download file (zip) <br />
[x] Download notebook as svg <br />
[ ] Download notebook as pdf <br />
[ ] Download annotated pdf <br />
[ ] Download ebub <br />
[ ] Create backup <br />
[ ] Sync Zotero -> Remarkable <br />
[ ] Sync Remarkable -> Zotero <br />
[ ] SSH to set sleep and suspend screen <br />
[ ] Search within documents (also handwritten)

## Ideas
[ ] Distributed Notebook (online locking if changed)

# Setup
For this installation we assume that python3, pip3 and all nvidia drivers
(GPU support) are already installed. Then execute the following
to create a virtual environment and install all necessary packages:

1. Create virtual environment: ```python3 -m venv env```
2. Activate venv: ```source env/bin/activate```
3. Update your pip installation: ```pip3 install --upgrade pip```
4. Install all requirements. Use requirements-gpu if a gpu is available, requirements-cpu otherwise: ```pip3 install -r requirements.txt```


# Acknowledgments
[1] Python remarkable api, https://github.com/subutux/rmapy <br />
[2] Golang remarkable tool, https://github.com/juruen/rmapi/ <br />
[3] Icons made by Freepik, Smashicons, Pixel Perfect, srip, Good ware, prettycons from www.flaticon.com <br />