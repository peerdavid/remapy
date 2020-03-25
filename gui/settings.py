
import tkinter as tk
import tkinter.ttk as ttk

import api.client as client

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

        label = tk.Label(root, text="    One-time code:")
        label.grid(row=2, column=1, sticky="W")
        self.entry_onetime_code_text = tk.StringVar()
        self.entry_onetime_code = tk.Entry(root, textvariable=self.entry_onetime_code_text)
        self.entry_onetime_code.grid(row=2, column=2, sticky="W")

        label = tk.Label(root, text="    Device token: ")
        label.grid(row=3, column=1, sticky="W")
        self.label_device_token = tk.Label(root, text="-")
        self.label_device_token.grid(row=3, column=2, sticky="W")

        label = tk.Label(root, text="    User token: ")
        label.grid(row=4, column=1, sticky="W")
        self.label_user_token = tk.Label(root, text="-")
        self.label_user_token.grid(row=4, column=2, sticky="W")

        self.btn_sign_in = tk.Button(root, text="SIGN IN", command=self.btn_sign_in_click, width=17)
        self.btn_sign_in.grid(row=5, column=2)

        label = tk.Label(root, text=" Zotero", font="Helvetica 14 bold")
        label.grid(row=6, column=1, sticky="W")

        # Subscribe to sign in event. Outer logic (i.e. main) can try to 
        # sign in automatically...
        self.rm_client.listen_sign_in(self)
    

    #
    # EVENT HANDLER
    #
    def sign_in_event_handler(self, event, config):
        if event == client.EVENT_SUCCESS:
            self.btn_sign_in.config(state = "disabled")
            self.label_device_token.config(text = config["device_token"])
            self.label_user_token.config(text = config["user_token"])
            self.entry_onetime_code.config(state = "disabled")
            self.entry_onetime_code_text.set(config["onetime_code"])
            
        elif event == client.EVENT_OFFLINE:
            self.btn_sign_in.config(state = "normal")
            # Message Offline
        else:
            self.btn_sign_in.config(state = "normal")
            # Message Failed


    def btn_sign_in_click(self):
        onetime_code = self.entry_onetime_code_text.get()
        self.rm_client.sign_in(onetime_code)
