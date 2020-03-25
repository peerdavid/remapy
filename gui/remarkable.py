import os
import subprocess
import tkinter as tk
import tkinter.ttk as ttk
from PIL import ImageTk as itk
from PIL import Image

import api.client as client
from api.client import Client
from api.rm2svg import rm2svg


class Remarkable(object):
    def __init__(self, root, rm_client, font_size=14, rowheight=14):
        self.nodes = dict()
        self.rm_client = rm_client

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

        self.tree["columns"]=("#1","#2")
        self.tree.column("#0", minwidth=250)
        self.tree.column("#1", width=180, minwidth=180, stretch=tk.NO)
        self.tree.column("#2", width=150, minwidth=150, stretch=tk.NO)

        self.tree.heading("#0",text="Name",anchor=tk.W)
        self.tree.heading("#1", text="Date modified",anchor=tk.W)
        self.tree.heading("#2", text="Status",anchor=tk.W)

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

        # Context menu on right click
        # Check out drag and drop: https://stackoverflow.com/questions/44887576/how-can-i-create-a-drag-and-drop-interface
        self.tree.bind("<Button-3>", self.tree_right_click)
        self.context_menu =tk.Menu(root, tearoff=0, font=font_size)
        self.context_menu.add_command(label='Open')
        self.context_menu.add_command(label='Download', command=self.btn_download_click)
        self.context_menu.add_command(label='Svg', command=self.btn_svg_click)
        self.context_menu.add_command(label='Move', command=self.btn_move_click)
        self.context_menu.add_command(label='Delete', command=self.btn_delete_click)

        self.tree.bind("<Double-1>", self.tree_double_click)


        # Footer
        self.lower_frame = tk.Frame(root)
        self.lower_frame.pack(side=tk.BOTTOM, anchor="w")

        self.search_text = tk.Entry(self.lower_frame)
        self.search_text.pack(side=tk.LEFT)

        self.btn = tk.Button(self.lower_frame, text="Filter")
        self.btn.pack(side = tk.LEFT)

        self.progressbar = ttk.Progressbar(self.lower_frame, orient="horizontal", length=200, mode="determinate")
        self.progressbar.pack(side = tk.LEFT, anchor="w")

        self.rm_client.listen_sign_in(self)


    
    def _update_tree(self, item):
        is_root = not item.is_document and item.parent is None

        if not is_root:
            image = self.icon_note if item.is_document else self.icon_dir
            pos = int(item.is_document)*10
            tree_id = self.tree.insert(
                item.parent.uuid, 
                pos, 
                item.uuid, 
                text=item.name, 
                values=(item.modified_str(), item.status), 
                image=image)

        for child in item.children:
            self._update_tree(child)


    #
    # EVENT HANDLER
    #
    def sign_in_event_handler(self, event, data):
        if event == client.EVENT_SUCCESS:
            self.root = self.rm_client.get_root()
            self._update_tree(self.root)


    #
    # EVENT HANDLER
    #
    def tree_right_click(self, event):
        self.selected_uuids = self.tree.selection()
        if self.selected_uuids:
            self.context_menu.tk_popup(event.x_root, event.y_root)   
            pass         
        else:
            # mouse pointer not over item
            pass

    
    def tree_double_click(self, event):
        self.selected_uuids = self.tree.selection()
        self.open_svg()

    def btn_delete_click(self):
        if not self.selected_uuids:
            return

        for iid in self.selected_uuids:
            self.tree.delete(iid)


    def btn_move_click(self):
        if not self.selected_uuids:
            return 

        for uuid in self.selected_uuids:
            self.tree.item(uuid, tags="move")


    def btn_download_click(self):
        for uuid in self.selected_uuids:
            item = self.rm_client.download_file(uuid)
            self.tree.item(uuid, values=(item.modified_str(), item.status))


    def btn_svg_click(self):
        self.open_svg()

    def open_svg(self):
        for uuid in self.selected_uuids:
            item = self.rm_client.get_item(uuid)

            if item.status != "Available":
                item = self.rm_client.download_file(uuid)

            rm_files_path = "%s/%s" % (item.path, item.uuid)
            out_path = "%s/%s_" % (item.path, item.name)
            rm2svg(rm_files_path, out_path, background="white")
            subprocess.call(('xdg-open', out_path + "00001.svg"))
