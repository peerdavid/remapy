# RemaPy Explorer

An open source explorer for your remarkable tablet to 
show, upload or delete files via the remarkable cloud. Although the RemaPy Explorer 
is only tested and evaluated on Linux, it should theoretically also 
work on Windows and / or Mac.

# ToDo's
 - [x] Authentication
 - [x] Settings page (Path to templates, sync folder, )
 - [x] About page
 - [x] List all folders and files
 - [x] Delete file
 - [x] Open collection (all files of collection with one click)
 - [x] Async backend to keep fronted reactive
 - [ ] Check and show if files are our of sync
 - [x] Download file (zip)
 - [x] Download notebook as pdf
 - [x] Download annotated pdf
 - [ ] Download ebub (without annotations)
 - [x] Upload pdf file
 - [ ] Upload ebub file
 - [ ] Upload raw zip file (i.e. restore from backup)
 - [ ] Create new folder
 - [ ] Create new notebook
 - [ ] Rename collection / documents
 - [ ] Move collection / documents
 - [ ] Better error handling
 - [ ] Logging
 - [ ] Test offline
 - [ ] Filter / Search documents
 - [ ] Delete local cache if doc is not available on remarkable 
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