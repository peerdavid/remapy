import os
import tkinter as tk
from tkinter import *
from tkinter import scrolledtext
import tkinter.ttk as ttk

from gui.remarkable import Remarkable
from gui.about import About

from api.client import Client


class Main(object):

    def __init__(self, window, rm_client):
        # Define app settings
        font_size = 38
        rowheight = 28
        window_width = 750
        window_height = 650

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
        self.notebook.add(frame, text="Backup", state="disabled")

        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Zotero", state="disabled")

        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Mirror", state="disabled")

        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="SSH", state="disabled")

        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Settings")
        
        frame = ttk.Frame(self.notebook)
        self.about = About(frame)
        self.notebook.add(frame, text="About")


def main():
    window = tk.Tk()

    rm_client = Client()
    app = Main(window, rm_client)

    window.mainloop()


if __name__ == '__main__':
    main()