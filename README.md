# RemaPy Explorer

RemaPy is an open source file explorer for your reMarkable tablet. You can upload documents via copy and paste from your local file explorer, open notebooks and annotated pdfs and delete documents or collections. RemaPy is written in Python and only tested on Linux,
altough it should (theoretically) also work on other systems. Feel free to 
write an issue if you find a bug or also if you have an idea for new features. 
A list of some todo's and future ideas that I want to implement is given below.

*WARNING:* This project is not affiliated with reMarkable AS, Oslo and you use this tool on your own risk.

![Explorer](doc/explorer.png)

# ToDo's
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
 - [ ] Upload raw zip file (i.e. restore from backup)
 - [ ] Create new folder
 - [ ] Create new notebook
 - [ ] Rename collection / documents
 - [ ] Move collection / documents
 - [ ] Better error handling
 - [ ] Logging
 - [ ] Test offline
 - [ ] Filter / Search documents
 - [ ] Delete local if doc is not available on remarkable 
 - [ ] Create installer


# Future ideas
 - [ ] Create full (or partially folder) backups of raw data
 - [ ] Backup viewer
 - [ ] Restore a backup into the cloud 
 - [ ] Select a collection to sync with Zotero
 - [ ] Search also for handwritten text
 - [ ] SSH access: Update background image, live view
 - [ ] Decrypt encrypted pdf's to be compatible with the RM


# How to setup / install RemaPy
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
[3] Icons made by Freepik, Smashicons, Pixel Perfect, iconixar  srip, Good ware, prettycons from www.flaticon.com <br />