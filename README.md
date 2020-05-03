# RemaPy Explorer

RemaPy is an open source file explorer for your reMarkable tablet. You can 
upload documents via copy and paste from your local file explorer, open 
notebooks and annotated pdfs and delete documents or collections. RemaPy 
is written in python and only tested on Linux, altough it should 
(theoretically) also work on other operating systems such as windows. 
A "how to install", the software architecture and FAQ's 
can be found in the [wiki](https://github.com/peerdavid/remapy/wiki).

*WARNING: This project is not affiliated to, 
nor endorsed by, reMarkable AS. I am not responsible for any 
damage done to your device or your data 
due to the use of this software.*


# Features 
<img src="doc/explorer.png" />

## Custom colors
Custom colors for individual layers are used by RemaPy for the rendering, 
if the layer name contains a '#' followed by a color name or 
[color hex code](https://www.color-hex.com/).
For example "Layer1 #ffee11" is rendered with hex color #ffee11 or "Layer 2 #red" 
is rendered in red. The hex code also support alpha values (e.g. #ffee11dd).
Therefore you can easily hide layers in the rendering process by setting the last
two values of the hex code to zero: #xxxxxx00.
<img src="doc/custom_colors.png" />

## Filter
You can use the filter (upper right) to display only a documents
that contain the given search string (not case sensitive). To search only 
for bookmarked icons, start your search string with "*". For example to 
search for all bookmarked documents that contain "remapy", enter "*remapy".

## Other features
 - Synchronization via the remarkable cloud
 - Show notebooks, annotated pdf's or annotated epub's
 - Show only the pages you annotated in a file
 - Show the original file without your annotations
 - Supports custom colors via layer names. 
 - Create backups of all your annotated documents
 - Upload pdf and epub via copy and paste from your file explorer
 - If you copy and paste a URL, a pdf of the given website is created and uploaded automatically



# Acknowledgments
[1] Python remarkable api, https://github.com/subutux/rmapy <br />
[2] Golang remarkable tool, https://github.com/juruen/rmapi/ <br />
[3] Icons made by Freepik, Smashicons, Pixel Perfect, iconixar  srip, 
Good ware, prettycons, Payungkead from www.flaticon.com <br />