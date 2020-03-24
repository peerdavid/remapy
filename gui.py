import os
import tkinter as tk
import tkinter.ttk as ttk
from PIL import ImageTk as itk
from PIL import Image

from api.client import Client


class App(object):
    def __init__(self, root, client, font_size=14):
        self.nodes = dict()
        self.client = client

        style = ttk.Style()
        style.configure("remapy.style.Treeview", highlightthickness=0, bd=0, font=('Calibri', font_size))
        style.configure("remapy.style.Treeview.Heading", font=('Calibri', font_size+2))
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
        
        self.icon_dir = Image.open("./icons/folder.png")
        self.icon_dir = self.icon_dir.resize((font_size, font_size))
        self.icon_dir = itk.PhotoImage(self.icon_dir)

        self.icon_note = Image.open("./icons/notebook.png")
        self.icon_note = self.icon_note.resize((font_size, font_size))
        self.icon_note = itk.PhotoImage(self.icon_note)

        self.icon_pdf = Image.open("./icons/pdf.png")
        self.icon_pdf = self.icon_pdf.resize((font_size, font_size))
        self.icon_pdf = itk.PhotoImage(self.icon_pdf)

        for i in range(5):
            # Level 1
            self.folder1 = self.tree.insert("", i, text=" Folder %d" % i, values=("22.03.2019 11:05","Folder","28%"), image=self.icon_dir)
            
            # Level 2
            self.tree.insert(self.folder1, "end", text=" C++", values=("15.01.2019 11:28","Notebook",""), image=self.icon_note)
            self.tree.insert(self.folder1, "end", text=" MachineLearning", values=("11.03.2019 11:29","Notebook","28%"), image=self.icon_note)
            self.tree.insert(self.folder1, "end", text=" ComputerVision", values=("15.03.2019 11:30","Notebook",""), image=self.icon_note)

        # Some other docs
        self.tree.insert("", 6, text=" Quick notes", values=("21.03.2019 11:25","Notebook",""), image=self.icon_note)
        self.tree.insert("", 7, text=" Paper", values=("21.03.2019 11:25","Pdf",""), image=self.icon_pdf)


        self.lower_frame = tk.Frame(root)
        self.lower_frame.pack(side=tk.BOTTOM, anchor="w")

        self.btn = tk.Button(self.lower_frame, text="LOG IN", command=self.btn_login_click)
        self.btn.pack(side = tk.LEFT)

        self.btn = tk.Button(self.lower_frame, text="Create Backup")
        self.btn.pack(side = tk.LEFT)

        self.btn = tk.Button(self.lower_frame, text="Cloud to local")
        self.btn.pack(side = tk.LEFT)

        self.btn = tk.Button(self.lower_frame, text="Zotero to Cloud")
        self.btn.pack(side = tk.LEFT)

        self.progressbar = ttk.Progressbar(self.lower_frame, orient="horizontal", length=200, mode="determinate")
        self.progressbar.pack(side = tk.LEFT, anchor="w")

        # Context menu on right click
        self.tree.bind("<Button-3>", self.popup_menu)
        self.context_menu =tk.Menu(root, tearoff=0, font=('Calibri', font_size))
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
    root = tk.Tk()
    client = Client()
    
    # ToDo: Save last position and sizes
    width, height = 750, 650
    x = (root.winfo_screenwidth() / 4 * 3) - (width / 2)
    y = (root.winfo_screenheight() / 2) - (height / 2)
    root.geometry("%dx%d+%d+%d" % (width, height, x, y))

    app = App(root, client)
    root.title("RemaPy")
    root.mainloop()


if __name__ == '__main__':
    main()