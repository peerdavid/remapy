
import tkinter as tk
import tkinter.ttk as ttk


class Settings(object):
    def __init__(self, root, rm_client, font_size):
        self.rm_client=rm_client

        root.grid_rowconfigure(1, minsize=50)
        root.grid_rowconfigure(2, minsize=30)
        root.grid_rowconfigure(3, minsize=30)
        root.grid_rowconfigure(4, minsize=30)
        root.grid_rowconfigure(6, minsize=50)
        
        label = tk.Label(root, text=" Authentication", font="Helvetica 14 bold")
        label.grid(row=1, column=1, sticky="W")

        label = tk.Label(root, text="    One time code:")
        label.grid(row=2, column=1, sticky="W")
        self.entry_onetime_code = tk.Entry(root)
        self.entry_onetime_code.grid(row=2, column=2, sticky="W")

        label = tk.Label(root, text="    Device token: ")
        label.grid(row=3, column=1, sticky="W")
        self.device_token = tk.Label(root, text="-")
        self.device_token.grid(row=3, column=2, sticky="W")

        label = tk.Label(root, text="    User token: ")
        label.grid(row=4, column=1, sticky="W")
        self.user_token = tk.Label(root, text="-")
        self.user_token.grid(row=4, column=2, sticky="W")

        self.btn = tk.Button(root, text="LOG IN", command=self.btn_login_click)
        self.btn.grid(row=5, column=2)

        label = tk.Label(root, text=" Zotero", font="Helvetica 14 bold")
        label.grid(row=6, column=1, sticky="W")

    def btn_login_click(self):
        self.rm_client.sign_in()