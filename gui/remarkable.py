import os
import subprocess
import tkinter as tk
import tkinter.ttk as ttk
from PIL import ImageTk as itk
from PIL import Image

import api.client
from api.client import Client
from api.object.item_factory import ItemFactory
from api.object.item import Item

class Remarkable(object):
    def __init__(self, root, font_size=14, rowheight=14):
        self.nodes = dict()
        self.rm_client = Client()
        self.item_factory = ItemFactory()

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
        self.tree.column("#2", width=150, minwidth=150, anchor="center", stretch=tk.NO)

        self.tree.heading("#0",text="Name", anchor="center")
        self.tree.heading("#1", text="Date modified", anchor="center")
        self.tree.heading("#2", text="Current Page", anchor="center")

        self.tree.tag_configure('move', background='#FF9800')    
        
        self.icon_collection = self._create_tree_icon("./icons/collection.png", rowheight)
        self.icon_note = self._create_tree_icon("./icons/notebook.png", rowheight)
        self.icon_pdf = self._create_tree_icon("./icons/pdf.png", rowheight)
        self.icon_book = self._create_tree_icon("./icons/book.png", rowheight)
        self.icon_cloud = self._create_tree_icon("./icons/cloud.png", rowheight)
        self.icon_unknown = self._create_tree_icon("./icons/unknown.png", rowheight)
        self.icon_sync = self._create_tree_icon("./icons/sync.png", rowheight)

        # Context menu on right click
        # Check out drag and drop: https://stackoverflow.com/questions/44887576/how-can-i-create-a-drag-and-drop-interface
        self.tree.bind("<Button-3>", self.tree_right_click)
        self.context_menu =tk.Menu(root, tearoff=0, font=font_size)
        self.context_menu.add_command(label='Open', command=self.btn_svg_click)
        self.context_menu.add_command(label='Download', command=self.btn_download_click)
        self.context_menu.add_command(label='Move', command=self.btn_move_click)
        self.context_menu.add_command(label='Delete', command=self.btn_delete_click)
        self.context_menu.add_command(label='Clear cache', command=self.btn_delete_click)

        self.tree.bind("<Double-1>", self.tree_double_click)


        # Footer
        self.lower_frame = tk.Frame(root)
        self.lower_frame.pack(side=tk.BOTTOM, anchor="w")

        btn = tk.Button(self.lower_frame, text="Sync")
        btn.pack(side = tk.LEFT)

        btn = tk.Button(self.lower_frame, text="Download")
        btn.pack(side = tk.LEFT)

        btn = tk.Button(self.lower_frame, text="Clear cache")
        btn.pack(side = tk.LEFT)
        
        self.search_text = tk.Entry(self.lower_frame)
        self.search_text.pack(side=tk.LEFT)

        self.btn = tk.Button(self.lower_frame, text="Filter")
        self.btn.pack(side = tk.LEFT)

        self.progressbar = ttk.Progressbar(self.lower_frame, orient="horizontal", length=200, mode="determinate")
        self.progressbar.pack(side = tk.LEFT, anchor="w")

        self.rm_client.listen_sign_in(self)


    def _create_tree_icon(self, path, row_height):
        icon = Image.open(path)
        icon = icon.resize((row_height-4, row_height-4))
        return itk.PhotoImage(icon)


    
    def _update_tree(self, item):
        is_root = not item.is_document and item.parent is None

        if not is_root:
            pos = int(item.is_document)*10
            tree_id = self.tree.insert(
                item.parent.uuid, 
                pos, 
                item.uuid)
            self._update_tree_item(item)

        for child in item.children:
            self._update_tree(child)



    #
    # EVENT HANDLER
    #
    def sign_in_event_handler(self, event, data):
        if event == api.client.EVENT_SUCCESS:
            self.root = self.item_factory.get_root()
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
            item = self.item_factory.get_item(uuid)
            self.download_files_recursively(item)
    

    def download_files_recursively(self, item):
        """ Download file or all child files if it is a folder
        """
        if item.is_document:
            self._sync_item(item, True)
            return

        for child in item.children:
            self.download_files_recursively(child)
    

    def _update_tree_item(self, item):
        image, current_page = self._get_item_tree_infos(item)
        self.tree.item(item.uuid, image=image, text=" " + item.name,
                       values=(item.modified_str(), current_page))


    def _get_item_tree_infos(self, item):
        image = self.icon_collection
        current_page = "-"

        if item.is_document:
            current_page = item.current_page
            if item.state == Item.STATE_UNKNOWN:
                image = self.icon_unknown
            elif item.state == Item.STATE_ONLINE:
                image = self.icon_cloud
            elif item.state == Item.STATE_SYNCED_OUT_OF_SYNC:
                image = self.icon_sync
            else:
                image = self.icon_note
            
        return image, current_page


    def _sync_item(self, item, force):    
        item.sync(force=force)
        self._update_tree_item(item)


    def tree_double_click(self, event):
        self.selected_uuids = self.tree.selection()
        self._open_svg()


    def btn_svg_click(self):
        self._open_svg()


    def _open_svg(self):
        for uuid in self.selected_uuids:
            item = self.item_factory.get_item(uuid)
            if not item.is_document:
                continue

            self._sync_item(item, False)
            subprocess.call(('xdg-open', item.current_svg_page))
    