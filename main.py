import os
import tkinter as tk
from tkinter import *
from tkinter import scrolledtext
import tkinter.ttk as ttk

from gui.remarkable import Remarkable
from gui.about import About
from gui.settings import Settings

import api.client as client
from api.client import Client


class Main(object):

    def __init__(self, window, rm_client):
        self.rm_client = rm_client

        # Define app settings
        font_size = 38
        rowheight = 28
        window_width = 750
        window_height = 650

        # Subscribe to events
        rm_client.listen_sign_in(self)

        # Window settings
        window.title("RemaPy")
        x = (window.winfo_screenwidth() / 4 * 3) - (window_width / 2)
        y = (window.winfo_screenheight() / 2) - (window_height / 2)
        window.geometry("%dx%d+%d+%d" % (window_width, window_height, x, y))

        # Create different tabs on notebook
        self.notebook = ttk.Notebook(window)
        self.notebook.pack(expand=1, fill="both")

        frame = ttk.Frame(self.notebook)
        self.remarkable = Remarkable(frame, rm_client, 
            font_size=font_size, rowheight=rowheight)
        self.notebook.add(frame, text="My Remarkable")

        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Backup", state="hidden")

        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Zotero", state="hidden")

        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Mirror", state="hidden")

        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="SSH", state="hidden")

        frame = ttk.Frame(self.notebook)
        self.settings = Settings(frame, rm_client, font_size)
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
        if event == client.EVENT_SUCCESS:
            self.notebook.tab(0, state="normal")
        elif event == client.EVENT_OFFLINE:
            pass # ToDo: We should show that we are offline...
        else:
            self.notebook.tab(0, state="disabled")


#
# M A I N
#
def main():
    window = tk.Tk()

    rm_client = Client()
    app = Main(window, rm_client)

    window.mainloop()


if __name__ == '__main__':
    main()