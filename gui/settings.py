from datetime import date
import time
import webbrowser
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import threading
from pathlib import Path

import api.remarkable_client
from api.remarkable_client import RemarkableClient
import utils.config as cfg
from model.item_manager import ItemManager

class Settings(object):
    def __init__(self, root, font_size):
        self.rm_client=RemarkableClient()
        self.item_manager = ItemManager()

        root.grid_columnconfigure(4, minsize=180)
        root.grid_rowconfigure(1, minsize=50)
        root.grid_rowconfigure(2, minsize=30)
        root.grid_rowconfigure(3, minsize=30)
        root.grid_rowconfigure(4, minsize=30)
        root.grid_rowconfigure(6, minsize=50)
        root.grid_rowconfigure(7, minsize=30)
        root.grid_rowconfigure(8, minsize=30)
        root.grid_rowconfigure(9, minsize=50)

        # gaps between columns
        label = tk.Label(root, text="    ")
        label.grid(row=1, column=1)
        label = tk.Label(root, text="    ")
        label.grid(row=1, column=3)
        label = tk.Label(root, text="  ")
        label.grid(row=1, column=5)

        label = tk.Label(root, text="Authentication", font="Helvetica 14 bold")
        label.grid(row=1, column=2, sticky="W")

        self.onetime_code_link = "https://my.remarkable.com#desktop"
        self.label_onetime_code = tk.Label(root, justify="left", anchor="w",
                    fg="blue", cursor="hand2", text="\nDownload one-time code from \n" + self.onetime_code_link)
        self.label_onetime_code.grid(row=2, column=7, sticky="SW")
        self.label_onetime_code.bind("<Button-1>", lambda e: webbrowser.open_new(self.onetime_code_link))

        label = tk.Label(root, justify="left", anchor="w", text="Status: ")
        label.grid(row=2, column=2, sticky="W")
        self.label_auth_status = tk.Label(root, text="Unknown")
        self.label_auth_status.grid(row=2, column=4, sticky="W")

        label = tk.Label(root, justify="left", anchor="w", text="One-time code:")
        label.grid(row=3, column=2, sticky="W")
        self.entry_onetime_code_text = tk.StringVar()
        self.entry_onetime_code = tk.Entry(root, textvariable=self.entry_onetime_code_text)
        self.entry_onetime_code.grid(row=3, column=4, sticky="W")

        self.btn_sign_in = tk.Button(root, text="Sign In", command=self.btn_sign_in_click, width=17)
        self.btn_sign_in.grid(row=4, column=4, sticky="W")

        label = tk.Label(root, text="General", font="Helvetica 14 bold")
        label.grid(row=6, column=2, sticky="W")

        label = tk.Label(root, text="Templates path:")
        label.grid(row=7, column=2, sticky="W")
        self.entry_templates_text = tk.StringVar()
        self.entry_templates_text.set(cfg.get("general.templates", default=""))
        self.entry_templates = tk.Entry(root, textvariable=self.entry_templates_text)
        self.entry_templates.grid(row=7, column=4, sticky="W")

        label = tk.Label(root, justify="left", anchor="w", text="A local folder that contains all template PNG files. \nYou can copy the template files from your tablet: \n'/usr/share/remarkable'")
        label.grid(row=7, column=7, sticky="W")

        label = tk.Label(root, text="Backup root path:")
        label.grid(row=8, column=2, sticky="W")
        self.backup_root_text = tk.StringVar()
        backup_root_default = Path.joinpath(Path.home(), "Backup","Remarkable")
        backup_root = cfg.get("general.backuproot", default=str(backup_root_default))
        self.backup_root_text.set(backup_root)
        self.entry_backup_root = tk.Entry(root, textvariable=self.backup_root_text)
        self.entry_backup_root.grid(row=8, column=4, sticky="W")

        label = tk.Label(root, justify="left", anchor="w", text="A local folder that will be used as the root folder for backups.")
        label.grid(row=8, column=7, sticky="W")

        self.btn_save = tk.Button(root, text="Save", command=self.btn_save_click, width=17)
        self.btn_save.grid(row=9, column=4, sticky="W")

        label = tk.Label(root, text="Backup", font="Helvetica 14 bold")
        label.grid(row=10, column=2, sticky="W")

        label = tk.Label(root, text="Backup path:")
        label.grid(row=11, column=2, sticky="W")
        self.backup_folder_text = tk.StringVar()

        backup_folder = str(date.today().strftime("%Y-%m-%d"))
        self.backup_folder_text.set(backup_folder)
        self.entry_backup_folder = tk.Entry(root, textvariable=self.backup_folder_text)
        self.entry_backup_folder.grid(row=11, column=4, sticky="W")

        self.label_backup_progress = tk.Label(root)
        self.label_backup_progress.grid(row=11, column=6)

        label = tk.Label(root, justify="left", anchor="w", text="Copy currently downloaded and annotated PDF files \ninto the given directory. Note that those files can not \nbe restored on the tablet.")
        label.grid(row=11, column=7, sticky="W")

        self.btn_create_backup = tk.Button(root, text="Create backup", command=self.btn_create_backup, width=17)
        self.btn_create_backup.grid(row=12, column=4, sticky="W")

        # Subscribe to sign in event. Outer logic (i.e. main) can try to
        # sign in automatically...
        self.rm_client.listen_sign_in_event(self)


    #
    # EVENT HANDLER
    #
    def sign_in_event_handler(self, event, config):

        self.btn_sign_in.config(state = "normal")
        self.entry_onetime_code.config(state="normal")
        self.btn_create_backup.config(state="disabled")
        self.btn_save.config(state="disabled")
        self.entry_backup_root.config(state="disabled")
        self.entry_backup_folder.config(state="disabled")
        self.entry_templates.config(state="disabled")

        if event == api.remarkable_client.EVENT_SUCCESS:
            self.btn_sign_in.config(state="disabled")
            self.entry_onetime_code.config(state="disabled")
            self.btn_create_backup.config(state="normal")
            self.btn_save.config(state="normal")
            self.entry_backup_root.config(state="normal")
            self.entry_backup_folder.config(state="normal")
            self.entry_templates.config(state="normal")
            self.label_auth_status.config(text="Successfully signed in", fg="green")

        elif event == api.remarkable_client.EVENT_USER_TOKEN_FAILED:
            self.label_auth_status.config(text="Could not renew user token\n(please try again).", fg="red")
            self.entry_onetime_code.config(state="disabled")

        elif event == api.remarkable_client.EVENT_ONETIMECODE_NEEDED:
            self.label_auth_status.config(text="Enter one-time code.", fg="red")

        else:
            self.label_auth_status.config(text="Could not sign in.", fg="red")


    def btn_sign_in_click(self):
        onetime_code = self.entry_onetime_code_text.get()
        self.rm_client.sign_in(onetime_code)



    def btn_save_click(self):
        general = {
            "templates": self.entry_templates_text.get(),
            "backuproot": self.backup_root_text.get()
        }
        cfg.save({"general": general})


    def btn_create_backup(self):
        message = "If your explorer is not synchronized, some files are not included in the backup. Should we continue?"
        result = messagebox.askquestion("Info", message, icon='warning')

        if result != "yes":
            return

        backup_root = self.backup_root_text.get()
        backup_folder = self.backup_folder_text.get()
        backup_path = Path.joinpath(Path(backup_root), backup_folder)
        self.label_backup_progress.config(text="Writing backup '%s'" % backup_path)

        def run():
            self.item_manager.create_backup(backup_path)
            self.label_backup_progress.config(text="")
            messagebox.showinfo("Info", "Successfully created backup '%s'" % backup_path)

        threading.Thread(target=run).start()

