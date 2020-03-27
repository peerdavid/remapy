import os
import subprocess
import threading
import shutil
import numpy as np
from pathlib import Path
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from PIL import ImageTk as itk
from PIL import Image

import api.client
from api.client import Client
from api.object.item_factory import ItemFactory
from api.object.item import Item
from api.object.document import Document


class Remarkable(object):
    def __init__(self, root, font_size=14, rowheight=14):
        
        self.root = root

        # Create tkinter elements
        self.nodes = dict()
        self.rm_client = Client()
        self.item_factory = ItemFactory()

        style = ttk.Style()
        style.configure("remapy.style.Treeview", highlightthickness=0, bd=0, font=font_size, rowheight=rowheight)
        style.configure("remapy.style.Treeview.Heading", font=font_size)
        style.layout("remapy.style.Treeview", [('remapy.style.Treeview.treearea', {'sticky': 'nswe'})])
        
        self.upper_frame = tk.Frame(root)
        self.upper_frame.pack(expand=True, fill=tk.BOTH)

        self.root.bind_all('<Control-v>', self.key_binding_paste)
        self.root.bind_all('<Return>', self.key_binding_return)
        self.root.bind_all('<Delete>', self.key_binding_delete)

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
        
        self.icons={}
        self.icons[Item.STATE_UNKNOWN] = self._create_tree_icon("./icons/unknown.png", rowheight)
        self.icons[Item.STATE_COLLECTION] = self._create_tree_icon("./icons/collection.png", rowheight)
        self.icons[Item.STATE_DOCUMENT_ONLINE] = self._create_tree_icon("./icons/document_online.png", rowheight)
        self.icons[Item.STATE_DOCUMENT_LOCAL_NOTEBOOK] = self._create_tree_icon("./icons/document_local_notebook.png", rowheight)
        self.icons[Item.STATE_DOCUMENT_LOCAL_PDF] = self._create_tree_icon("./icons/document_local_pdf.png", rowheight)
        self.icons[Item.STATE_DOCUMENT_LOCAL_EBUB] = self._create_tree_icon("./icons/document_local_ebub.png", rowheight)
        self.icons[Item.STATE_DOCUMENT_OUT_OF_SYNC] = self._create_tree_icon("./icons/document_local_out_of_sync.png", rowheight)
        self.icons[Item.STATE_DOCUMENT_DOWNLOADING] = self._create_tree_icon("./icons/document_downloading.png", rowheight)

        # Context menu on right click
        # Check out drag and drop: https://stackoverflow.com/questions/44887576/how-can-i-create-a-drag-and-drop-interface
        self.tree.bind("<Button-3>", self.tree_right_click)
        self.context_menu =tk.Menu(root, tearoff=0, font=font_size)
        self.context_menu.add_command(label='Open', command=self.btn_open_click)
        self.context_menu.add_command(label='Download', command=self.btn_download_async_click)
        self.context_menu.add_command(label='Clear cache', command=self.btn_clear_cache_click)
        self.context_menu.add_command(label='Delete', command=self.btn_delete_async_click)
        self.context_menu.add_separator()
        self.context_menu.add_command(label='Copy')
        self.context_menu.add_command(label='Paste', command=self.btn_paste_async_click)
        self.context_menu.add_command(label='Cut')

        self.tree.bind("<Double-1>", self.tree_double_click)


        # Footer
        self.lower_frame = tk.Frame(root)
        self.lower_frame.pack(side=tk.BOTTOM, anchor="w")

        btn = tk.Button(self.lower_frame, text="Sync")
        btn.pack(side = tk.LEFT)

        btn = tk.Button(self.lower_frame, text="Download")
        btn.pack(side = tk.LEFT)

        btn = tk.Button(self.lower_frame, text="Clear cache", command=self.btn_clear_all_cache_click)
        btn.pack(side = tk.LEFT)
        
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

            item.add_state_listener(self._update_tree_item)    

        for child in item.children:
            self._update_tree(child)



    #
    # EVENT HANDLER
    #
    def sign_in_event_handler(self, event, data):
        if event == api.client.EVENT_SUCCESS:
            root = self.item_factory.get_root()
            self._update_tree(root)


    #
    # EVENT HANDLER
    #
    def tree_right_click(self, event):
        selected_uuids = self.tree.selection()
        if selected_uuids:
            items = [self.item_factory.get_item(uuid) for uuid in selected_uuids]
            for item in items:
                for possile_child in items:
                    if not item.is_parent_of(possile_child):
                        continue 
                    
                    messagebox.showerror(
                        "Invalid operation", 
                        "Your selection is invalid. You can not perform an \
                            action on a folder and one of its child items.")
                    return

            self.context_menu.tk_popup(event.x_root, event.y_root)   
            pass         
        else:
            # mouse pointer not over item
            pass
        

    def key_binding_delete(self, event):
        self.btn_delete_async_click()

    def btn_delete_async_click(self):
        selected_uuids = self.tree.selection()
        items = [self.item_factory.get_item(uuid) for uuid in selected_uuids]
        
        count = [0, 0]
        for item in items:
            if item.is_document:
                count[0] += 1
                continue
            
            child_count = item.get_exact_children_count()
            count = np.add(count, child_count)
        
        message = "Do you really want to delete %d collection(s) and %d file(s)?" % (count[1], count[0])
        result = messagebox.askquestion("Delete", message, icon='warning')

        if result != "yes":
            return

        def run():
            for item in items:
                item.delete()
        threading.Thread(target=run).start()
            
    

    def btn_clear_cache_click(self):
        selected_uuids = self.tree.selection()
        for uuid in selected_uuids:
            self.item_factory.depth_search(
                fun = lambda item: item.clear_cache(),
                item = self.item_factory.get_item(uuid)
        )


    def btn_download_async_click(self):
        selected_uuids = self.tree.selection()
        
        def run():
            for uuid in selected_uuids:
                self.item_factory.depth_search(
                    fun = lambda i: self._sync_item(i, True),
                    item = self.item_factory.get_item(uuid)
                )
        threading.Thread(target=run).start()
    

    def _update_tree_item(self, item):
        if item.state == Item.STATE_DELETED:
            self.tree.delete(item.uuid)
        else:
            self.tree.item(
                item.uuid, 
                image=self.icons[item.state], 
                text=" " + item.name,
                values=(item.modified_str(), item.current_page))


    def _sync_item(self, item, force):   
        item.sync(force=force)


    def tree_double_click(self, event):
        selected_uuids = self.tree.selection()
        item = self.item_factory.get_item(selected_uuids[0])
        
        if item.is_document:
            self._open_async()


    def key_binding_return(self, event):
        self._open_async()


    def btn_open_click(self):
        self._open_async()

    def btn_clear_all_cache_click(self):
        # Clean everything, also if some (old) things exist
        shutil.rmtree(Document.PATH, ignore_errors=True)
        Path(Document.PATH).mkdir(parents=True, exist_ok=True)

        self.item_factory.depth_search(
            fun=lambda item: item.update_state()
        )


    def _open_async(self):
        selected_uuids = self.tree.selection()
        def open_uuid(item):
            for child in item.children:
                open_uuid(child)
            
            if not item.is_document:
                return

            self._sync_item(item, False)

            if item.state == Item.STATE_DOCUMENT_LOCAL_NOTEBOOK:
                subprocess.call(('xdg-open', item.path_annotated_pdf))
            elif item.state == Item.STATE_DOCUMENT_LOCAL_PDF:
                subprocess.call(('xdg-open', item.path_annotated_pdf))


        def open_all_uuids():
            for uuid in selected_uuids:
                item = self.item_factory.get_item(uuid)
                open_uuid(item)

        threading.Thread(target=open_all_uuids).start()
        

    #
    # Copy, Paste, Cut
    #
    def key_binding_paste(self, event):
        self.btn_paste_async_click()

    def btn_paste_async_click(self):
        file_path = self.root.clipboard_get()
        if not os.path.exists(file_path):
            messagebox.showerror("Paste error", "No file found to upload.")
            return
        
        if not file_path.endswith(".pdf"):
            messagebox.showerror("Paste error", "Only .pdf files are supported.")
            return
        
        print("Upload file")
