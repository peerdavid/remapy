# RemaPy Explorer

RemaPy is an open source file explorer for your reMarkable tablet. You can upload documents via copy and paste from your local file explorer, open notebooks and annotated pdfs and delete documents or collections. RemaPy is written in Python and only tested on Linux,
altough it should (theoretically) also work on other systems. Feel free to 
write an issue if you find a bug or also if you have an idea for new features. 
A list of some todo's and future ideas that I want to implement is given below.

*WARNING:* This project is not affiliated to, nor endorsed by, reMarkable AS. 
I am not responsible for any damage done to your device or your data 
due to the use of this software.

<img src="doc/explorer.png" />
Ps.: Image created with RemaPy ;)

# Features
 - Synchronization via the remarkable cloud
 - Open notebooks, annotated pdf's or annotated epub's
 - Open only the pages that you annotated
 - Open the original file without annotations
 - Create backups of your annotated documents
 - Upload pdf and epub via copy and paste from your file explorer
 - Upload a webpage simply via copy and paste (copy and paste a url instead of a file)


# How to setup / install RemaPy
First of all ensure that python3 (>= 3.6) and pip3 is installed.

## Linux
Clone this repository to a local folder. To install all 
dependencies into a virtual environment, execute steps 1-4. 
If you want to install the packages system wide, execute only step 4:
1. Create virtual environment: ```python3 -m venv env```
2. Activate venv: ```source env/bin/activate```
3. Update your pip installation: ```pip3 install --upgrade pip```
4. Install all requirements. Use requirements-gpu if a gpu is available, requirements-cpu otherwise: ```pip3 install -r requirements.txt```

You can then simply execute remapy with ```./rema.py```

Note: To create a launcher symbol adapt the remapy.desktop file and copy it 
to ~/.local/share/applications/remapy.desktop


## Windows
Coming soon...



# FAQ
**How can I upload a document?**<br />
Simply copy the file in your explorer and paste it in RemaPy. If you 
paste a URL instead of a webpage, the webpage will be downloaded, converted
to pdf and uploaded onto your tablet. <br />

**Why are annotations different than on my talbet / the original client?**<br />
My main motivation to write RemaPy was, to enable linux users to read their 
notebooks, annotated pdf's and annotated epubs via the remarkable cloud. 
Especially researches and students often use linux and RemaPy is somehow designed
for those users. Therefore the rendering as its done by the original 
client and by the remarkable tablet is honestly not on my roadmap. 
Feel free to write an issue or even better improve the renderer (```models/render.py```) 
. Any help is welcome :) <br />

**Why are uploaded webpages sometimes only the "terms of use" page?** <br />
This is currently a restriction and until now I had not really a good idea 
how I can *generally* overcome this problem i.e. convert the webpage to 
a pdf after the terms of use are accepted. Any idea is welcome :) <br />



# Roadmap
Here you can find what I have done so far and my next todo's:

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
 - [x] Render only pages with annotations
 - [x] Toggle bookmark
 - [ ] Let the user select annotation colors
 - [ ] Show bookmark
 - [ ] Upload folder / multiple files recursively
 - [ ] Filter / Search documents or folders
 - [ ] Rename
 - [ ] Create new
 - [ ] Move
 - [ ] Better error handling
 - [ ] Better logging
 - [ ] Refactoring and cleanup
 - [ ] Zotero sync
 - [ ] SSH access: Change background image of remarkable
 - [ ] OCR; Search in documents text and handwritten notes


# Acknowledgments
[1] Python remarkable api, https://github.com/subutux/rmapy <br />
[2] Golang remarkable tool, https://github.com/juruen/rmapi/ <br />
[3] Icons made by Freepik, Smashicons, Pixel Perfect, iconixar  srip, 
Good ware, prettycons, Payungkead from www.flaticon.com <br />