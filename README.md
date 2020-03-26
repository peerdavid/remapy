# RemaPy

An open source tool to manage documents of your remarkable tablet.
This tool provides a gui as well as an easy to use python api to write 
simple scripts. Although it is only tested and evaluated on Linux, 
it should (theoretically) also work on Windows and/or Mac.

# ToDo's
 - [x] Authentication <br />
 - [x] Settings page (Path to templates, sync folder, ) <br />
 - [x] About page <br />
 - [x] List all folders and files <br />
 - [ ] Delete file <br />
 - [ ] Upload file <br />
 - [x] Async backend to keep fronted reactive <br />
 - [ ] Make tool offline ready <br />
 - [x] Download file (zip) <br />
 - [x] Download notebook as svg <br />
 - [ ] Download notebook as pdf <br />
 - [ ] Download annotated pdf <br />
 - [ ] Select specific layers when creating notes <br />
 - [ ] Download ebub <br />
 - [ ] Filter some documents <br />


# Future ideas
 - [ ] Create full (or partially folder) backups of raw data <br />
 - [ ] Backup viewer <br />
 - [ ] Restore a backup into the cloud <br /> 
 - [ ] Sync with Zotero <br />
 - [ ] Search also for handwritten text
 - [ ] SSH: Update background etc. <br />


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