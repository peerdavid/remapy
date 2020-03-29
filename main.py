#!/usr/bin/env python3

import os
from pathlib import Path
import tkinter as tk
from tkinter import *
from tkinter import scrolledtext
import tkinter.ttk as ttk

from gui.remarkable import Remarkable
from gui.about import About
from gui.settings import Settings

import api.remarkable_client
from api.remarkable_client import RemarkableClient
import utils.config

class Main(object):

    def __init__(self, window):
        self.rm_client = RemarkableClient()

        # Define app settings
        font_size = 38
        rowheight = 28
        window_width = 750
        window_height = 650

        # Subscribe to events
        self.rm_client.listen_sign_in(self)

        # Window settings
        window.title("RemaPy Explorer")
        x = (window.winfo_screenwidth() / 4 * 3) - (window_width / 2)
        y = (window.winfo_screenheight() / 2) - (window_height / 2)
        window.geometry("%dx%d+%d+%d" % (window_width, window_height, x, y))

        # Create different tabs on notebook
        self.notebook = ttk.Notebook(window)
        self.notebook.pack(expand=1, fill="both")

        frame = ttk.Frame(self.notebook)
        self.remarkable = Remarkable(frame, window, font_size=font_size, rowheight=rowheight)
        self.notebook.add(frame, text="File Explorer")

        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Backup", state="hidden")

        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Zotero", state="hidden")

        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Mirror", state="hidden")

        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="SSH", state="hidden")

        frame = ttk.Frame(self.notebook)
        self.settings = Settings(frame, font_size)
        self.notebook.add(frame, text="Settings")
        
        frame = ttk.Frame(self.notebook)
        self.about = About(frame)
        self.notebook.add(frame, text="About")

        # Try to sign in to the rm cloud without a onetime code i.e. we 
        # assume that the user token is already available. If it is not 
        # possible we get a signal to disable "My remarkable" and settings
        # are shown...
        self.rm_client.sign_in()
        

    #
    # EVENT HANDLER
    #
    def sign_in_event_handler(self, event, data):
        if event == api.remarkable_client.EVENT_SUCCESS:
            self.notebook.tab(0, state="normal")
        else:
            self.notebook.tab(0, state="disabled")


#
# M A I N
#
def main():
    window = tk.Tk(className="RemaPy")
    Path(utils.config.PATH).mkdir(parents=True, exist_ok=True)
    app = Main(window)
    window.mainloop()


if __name__ == '__main__':
    main()