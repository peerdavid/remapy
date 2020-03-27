
import webbrowser
import tkinter as tk
import tkinter.ttk as ttk

import api.client
from api.client import Client
import api.config as cfg


class Settings(object):
    def __init__(self, root, font_size):
        self.rm_client=Client()

        root.grid_columnconfigure(4, minsize=180)
        root.grid_rowconfigure(1, minsize=50)
        root.grid_rowconfigure(2, minsize=30)
        root.grid_rowconfigure(3, minsize=30)
        root.grid_rowconfigure(4, minsize=30)
        root.grid_rowconfigure(6, minsize=50)
        
        # gaps between columns
        label = tk.Label(root, text="    ")
        label.grid(row=1, column=1)
        label = tk.Label(root, text="    ")
        label.grid(row=1, column=3)
        label = tk.Label(root, text="  ")
        label.grid(row=1, column=5)

        label = tk.Label(root, text="Authentication", font="Helvetica 14 bold")
        label.grid(row=1, column=2, sticky="W")

        self.onetime_code_link = "https://my.remarkable.com/connect/remarkable"
        self.label_onetime_code = tk.Label(root, fg="blue", cursor="hand2")
        self.label_onetime_code.grid(row=2, column=6)
        self.label_onetime_code.bind("<Button-1>", lambda e: webbrowser.open_new(self.onetime_code_link))

        label = tk.Label(root, text="Status: ")
        label.grid(row=2, column=2, sticky="W")
        self.label_auth_status = tk.Label(root, text="Unknown")
        self.label_auth_status.grid(row=2, column=4, sticky="W")

        label = tk.Label(root, text="One-time code:")
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

        self.btn_save_ = tk.Button(root, text="Save", command=self.btn_save_click, width=17)
        self.btn_save_.grid(row=8, column=4, sticky="W")

        # Subscribe to sign in event. Outer logic (i.e. main) can try to 
        # sign in automatically...
        self.rm_client.listen_sign_in(self)
    

    #
    # EVENT HANDLER
    #
    def sign_in_event_handler(self, event, config):

        self.btn_sign_in.config(state = "normal")
        self.entry_onetime_code.config(state="normal")
        self.label_onetime_code.config(text="")

        if event == api.client.EVENT_SUCCESS:
            self.btn_sign_in.config(state="disabled")
            self.label_auth_status.config(text="Successfully signed in", fg="green")
            self.entry_onetime_code.config(state="disabled")
            
        elif event == api.client.EVENT_USER_TOKEN_FAILED:
            self.label_auth_status.config(text="Could not renew user token (please try again).", fg="red")
            self.entry_onetime_code.config(state="disabled")

        elif event == api.client.EVENT_ONETIMECODE_NEEDED:
            self.label_auth_status.config(text="Enter one-time code from:", fg="red")
            self.label_onetime_code.config(text=self.onetime_code_link)
        
        elif event == api.client.EVENT_USER_TOKEN_FAILED:
            self.label_auth_status.config(text="Could not fetch device token (please try again).", fg="red")
            
        else:
            self.label_auth_status.config(text="Sorry, an error occurred.", fg="red")


    def btn_sign_in_click(self):
        onetime_code = self.entry_onetime_code_text.get()
        self.rm_client.sign_in(onetime_code)
    

    def btn_save_click(self):
        general = {
            "templates": self.entry_templates_text.get()
        }
        cfg.save({"general": general})
