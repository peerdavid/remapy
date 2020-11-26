#!/usr/bin/env python3

import os
import utils.config as cfg
from pathlib import Path
import tkinter as tk
from tkinter import *
from tkinter import scrolledtext
import tkinter.ttk as ttk

from gui.file_explorer import FileExplorer
from gui.about import About
from gui.settings import Settings

import api.remarkable_client
from api.remarkable_client import RemarkableClient
import utils.config

class Main(object):

    def __init__(self, window):
        self.rm_client = RemarkableClient()

        # Define app settings
        scale=cfg.get("scaling",1/window.tk.call('tk', 'scaling'))
        print(scale)
        window.tk.call('tk', 'scaling',1/scale)
        font_size = int(38*scale)
        row_height = int(30*scale)
        window_width = 750*scale
        window_height = 650*scale

        # Subscribe to events
        self.rm_client.listen_sign_in_event(self)

        # Window settings
        window.title("RemaPy Explorer")

        # Try to start remapy always on the first screen and in the middle.
        # We assume a resolution width of 1920... if 1920 is too large use
        # the real resolution
        x = min(window.winfo_screenwidth(), 1920) / 2 - (window_width / 2)
        y = (window.winfo_screenheight() / 2) - (window_height / 2)
        window.geometry("%dx%d+%d+%d" % (window_width, window_height, x, y))

        # Create different tabs on notebook
        self.notebook = ttk.Notebook(window)
        self.notebook.pack(expand=1, fill="both")

        frame = ttk.Frame(self.notebook)
        self.file_explorer = FileExplorer(frame, window, font_size=font_size, row_height=row_height)
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
        # If we fail to get a user token, we are e.g. offline. So we continue
        # and try if we can get it later; otherwise we go into an offline mode
        if event == api.remarkable_client.EVENT_SUCCESS or event == api.remarkable_client.EVENT_USER_TOKEN_FAILED:
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
