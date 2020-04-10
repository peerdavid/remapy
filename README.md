# RemaPy Explorer

RemaPy is an open source file explorer for your reMarkable tablet. You can upload documents via copy and paste from your local file explorer, open notebooks and annotated pdfs and delete documents or collections. RemaPy is written in Python and only tested on Linux,
altough it should (theoretically) also work on other systems. Feel free to 
write an issue if you find a bug or also if you have an idea for new features. 
A list of some todo's and future ideas that I want to implement is given below.

*WARNING:* This project is not affiliated with reMarkable AS, Oslo and you use this tool on your own risk.

<img src="doc/explorer.png" />


## Features
 - Open annotated or original file (without annotations)
 - Open remarkable raw files
 - Colored annotations
 - Upload pdf and epub via copy and paste
 - Create backups of all your files (pdf only)
 - Upload a webpage via copy and paste (simply paste a url in remapy)


# How to setup / install RemaPy
First of all ensure that python3 and pip3 is installed.

## Linux
To install all dependencies into a virtual environment, execute steps 1-4. 
If you want to install the packages system wide, execute only step 4:
1. Create virtual environment: ```python3 -m venv env```
2. Activate venv: ```source env/bin/activate```
3. Update your pip installation: ```pip3 install --upgrade pip```
4. Install all requirements. Use requirements-gpu if a gpu is available, requirements-cpu otherwise: ```pip3 install -r requirements.txt```

To create a launcher symbol adapt the remapy.desktop file and copy it 
to ~/.local/share/applications/remapy.desktop


## Windows
Coming soon...


# ToDo's
There are still some things that I want to implement:

 - [x] Authentication
 - [x] Settings page (Path to templates, sync folder, )
 - [x] About page
 - [x] List all folders and files
 - [x] Delete file
 - [x] Open collection (all files of collection with one click)
 - [x] Async backend to keep fronted reactive
 - [x] Check and show if files are our of sync
 - [x] Download file (zip)
 - [x] Download notebook as pdf
 - [x] Download annotated pdf
 - [x] Download epub (without annotations)
 - [x] Download epub (with annotations as pdf)
 - [x] Upload pdf file
 - [x] Upload epub file
 - [x] Show download progress bar
 - [x] Better rendering for highlighter
 - [x] Use multiple threads to download and render documents (speed up)
 - [x] Show sync state also on collection level
 - [x] Show icon while uploading a file
 - [x] Backup annotated files
 - [x] Alphabetic order of collections and documents in tree
 - [x] Make RemaPy offline ready (readonly)
 - [x] Delete local if doc is not available on remarkable 
 - [x] Copy and past a webpage (upload as pdf)
 - [ ] Render only marked text and images and export into odt file
 - [ ] Show cloud symbol also on collection if some docs are not synced
 - [ ] Upload folders / multiple files (create folders and all pdf files of this folder)
 - [ ] Filter / Search documents or folders
 - [ ] Rename collection
 - [ ] Rename document
 - [ ] Create new collection
 - [ ] Create new notebook
 - [ ] Move collection
 - [ ] Move document
 - [ ] Better error handling
 - [ ] Better logging
 - [ ] Refactoring and cleanup
 - [ ] Set exact versions of python packages in requirements.txt
 - [ ] Zotero sync
 - [ ] SSH access: Change background image of remarkable, live view via ssh
 - [ ] OCR; Search in documents text and handwritten notes
 - [ ] Decrypt encrypted pdf's before uploading it to be compatible with the RM
 - [ ] Select colors for rendering of pens and highlighter


# Acknowledgments
[1] Python remarkable api, https://github.com/subutux/rmapy <br />
[2] Golang remarkable tool, https://github.com/juruen/rmapi/ <br />
[3] Icons made by Freepik, Smashicons, Pixel Perfect, iconixar  srip, 
Good ware, prettycons, Payungkead from www.flaticon.com <br />