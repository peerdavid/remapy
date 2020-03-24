import os
import tkinter as tk
from tkinter import *
from tkinter import scrolledtext
import tkinter.ttk as ttk
from PIL import ImageTk as itk
from PIL import Image

import about
from api.client import Client


class MyRemarkable(object):
    def __init__(self, root, client, font_size=14, rowheight=14):
        self.nodes = dict()
        self.client = client

        style = ttk.Style()
        style.configure("remapy.style.Treeview", highlightthickness=0, bd=0, font=font_size, rowheight=rowheight)
        style.configure("remapy.style.Treeview.Heading", font=font_size)
        style.layout("remapy.style.Treeview", [('remapy.style.Treeview.treearea', {'sticky': 'nswe'})])
        
        self.upper_frame = tk.Frame(root)
        self.upper_frame.pack(expand=True, fill=tk.BOTH)

        # Add tree and scrollbars
        self.tree = ttk.Treeview(self.upper_frame, style="remapy.style.Treeview")
        self.tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        
        self.vsb = ttk.Scrollbar(self.upper_frame, orient="vertical", command=self.tree.yview)
        self.vsb.pack(side=tk.LEFT, fill='y')
        self.tree.configure(yscrollcommand=self.vsb.set)

        self.hsb = ttk.Scrollbar(root, orient="horizontal", command=self.tree.xview)
        self.hsb.pack(fill='x')
        self.tree.configure(xscrollcommand=self.hsb.set)

        self.tree["columns"]=("#1","#2","#3")
        self.tree.column("#0", width=270, minwidth=270)
        self.tree.column("#1", width=150, minwidth=150, stretch=tk.NO)
        self.tree.column("#2", width=200, minwidth=100, stretch=tk.NO)
        self.tree.column("#3", width=80, minwidth=50, stretch=tk.NO)

        self.tree.heading("#0",text="Name",anchor=tk.W)
        self.tree.heading("#1", text="Date modified",anchor=tk.W)
        self.tree.heading("#2", text="Type",anchor=tk.W)
        self.tree.heading("#3", text="Size",anchor=tk.W)

        self.tree.tag_configure('move', background='#FF9800')    
        
        icon_size = rowheight-4
        self.icon_dir = Image.open("./icons/folder.png")
        self.icon_dir = self.icon_dir.resize((icon_size, icon_size))
        self.icon_dir = itk.PhotoImage(self.icon_dir)

        self.icon_note = Image.open("./icons/notebook.png")
        self.icon_note = self.icon_note.resize((icon_size, icon_size))
        self.icon_note = itk.PhotoImage(self.icon_note)

        self.icon_pdf = Image.open("./icons/pdf.png")
        self.icon_pdf = self.icon_pdf.resize((icon_size, icon_size))
        self.icon_pdf = itk.PhotoImage(self.icon_pdf)

        self.icon_book = Image.open("./icons/book.png")
        self.icon_book = self.icon_book.resize((icon_size, icon_size))
        self.icon_book = itk.PhotoImage(self.icon_book)

        for i in range(5):
            # Level 1
            self.folder1 = self.tree.insert("", i, text=" Folder %d" % i, values=("22.03.2019 11:05","Folder","28%"), image=self.icon_dir)
            
            # Level 2
            another_folder = self.tree.insert(self.folder1, "end", text=" Something", values=("15.03.2019 11:30","Folder",""), image=self.icon_dir)
            self.tree.insert(self.folder1, "end", text=" C++", values=("15.01.2019 11:28","Ebub",""), image=self.icon_book)
            self.tree.insert(self.folder1, "end", text=" MachineLearning", values=("11.03.2019 11:29","Pdf","28%"), image=self.icon_pdf)

            self.tree.insert(another_folder, "end", text=" ComputerVision", values=("15.03.2019 11:30","Notebook",""), image=self.icon_note)

        # Some other docs
        self.tree.insert("", 6, text=" Quick notes", values=("21.03.2019 11:25","Notebook",""), image=self.icon_note)
        self.tree.insert("", 7, text=" Paper", values=("21.03.2019 11:25","Pdf",""), image=self.icon_pdf)


        self.lower_frame = tk.Frame(root)
        self.lower_frame.pack(side=tk.BOTTOM, anchor="w")

        self.search_text = tk.Entry(self.lower_frame)
        self.search_text.pack(side=LEFT)

        self.btn = tk.Button(self.lower_frame, text="Filter")
        self.btn.pack(side = tk.LEFT)


        self.progressbar = ttk.Progressbar(self.lower_frame, orient="horizontal", length=200, mode="determinate")
        self.progressbar.pack(side = tk.LEFT, anchor="w")

        self.btn = tk.Button(self.lower_frame, text="LOG IN", command=self.btn_login_click)
        self.btn.pack(side = tk.LEFT)


        # Context menu on right click
        self.tree.bind("<Button-3>", self.popup_menu)
        self.context_menu =tk.Menu(root, tearoff=0, font=font_size)
        self.context_menu.add_command(label='Open')
        self.context_menu.add_command(label='Download', command=self.btn_download_click)
        self.context_menu.add_command(label='Download Raw', command=self.btn_download_raw_click)
        self.context_menu.add_command(label='Move', command=self.btn_move_click)
        self.context_menu.add_command(label='Delete', command=self.btn_delete_click)
        

        # Check out drag and drop: https://stackoverflow.com/questions/44887576/how-can-i-create-a-drag-and-drop-interface
    
    def btn_login_click(self):
        self.client.sign_in()

    def popup_menu(self, event):
        """action in event of button 3 on tree view"""
        # select row under mouse
        #self.iid = self.tree.identify_row(event.y)
        self.iids = self.tree.selection()
        if self.iids:
            # mouse pointer over item
            self.context_menu.tk_popup(event.x_root, event.y_root)   
            pass         
        else:
            # mouse pointer not over item
            # occurs when items do not fill frame
            # no action required
            pass

    def btn_delete_click(self):
        if not self.iids:
            return

        for iid in self.iids:
            self.tree.delete(iid)

    def btn_move_click(self):
        if not self.iids:
            return 

        for iid in self.iids:
            self.tree.item(iid, tags="move")

    def btn_download_click(self):
        self.progressbar.start()

    def btn_download_raw_click(self):
        self.progressbar.stop()
        


def main():
    form = tk.Tk()
    form.title("RemaPy")
    font_size = 38
    rowheight = 28

    tabs = ttk.Notebook(form)
    tabs.pack(expand=1, fill="both")
    
    width, height = 750, 650
    x = (form.winfo_screenwidth() / 4 * 3) - (width / 2)
    y = (form.winfo_screenheight() / 2) - (height / 2)
    form.geometry("%dx%d+%d+%d" % (width, height, x, y))

    # Create my remarkable tab
    rm_client = Client()
    rm_frame = ttk.Frame(tabs)
    MyRemarkable(rm_frame, rm_client, font_size=font_size, rowheight=rowheight)
    tabs.add(rm_frame, text="My Remarkable")

    frame = ttk.Frame(tabs)
    tabs.add(frame, text="Backup", state="disabled")

    frame = ttk.Frame(tabs)
    tabs.add(frame, text="Zotero", state="disabled")

    frame = ttk.Frame(tabs)
    tabs.add(frame, text="Mirror", state="disabled")

    frame = ttk.Frame(tabs)
    tabs.add(frame, text="SSH", state="disabled")

    frame = ttk.Frame(tabs)
    tabs.add(frame, text="Settings")

    frame = ttk.Frame(tabs)
    about_text = tk.scrolledtext.ScrolledText(frame)
    about_text.insert("1.0", about.ABOUT)
    about_text.config(state=tk.DISABLED)
    about_text.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    tabs.add(frame, text="About")

    form.mainloop()


if __name__ == '__main__':
    main()