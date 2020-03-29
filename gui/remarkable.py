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

import api.remarkable_client
from api.remarkable_client import RemarkableClient
from model.item_factory import ItemFactory
from model.item import Item
import model.document
from model.document import Document, create_document_zip
import utils.config

class Remarkable(object):
    def __init__(self, root, window, font_size=14, rowheight=14):
        
        self.root = root

        # Create tkinter elements
        self.nodes = dict()
        self.rm_client = RemarkableClient()
        self.item_factory = ItemFactory()

        style = ttk.Style()
        style.configure("remapy.style.Treeview", highlightthickness=0, bd=0, font=font_size, rowheight=rowheight)
        style.configure("remapy.style.Treeview.Heading", font=font_size)
        style.layout("remapy.style.Treeview", [('remapy.style.Treeview.treearea', {'sticky': 'nswe'})])
        
        self.upper_frame = tk.Frame(root)
        self.upper_frame.pack(expand=True, fill=tk.BOTH)

        window.bind('<Control-v>', self.key_binding_paste)
        window.bind('<Control-c>', self.key_binding_copy)
        window.bind('<Return>', self.key_binding_return)
        window.bind('<Delete>', self.key_binding_delete)

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
        
        self.icon_cloud = self._create_tree_icon("./gui/icons/cloud.png", rowheight)
        self.icon_syncing = self._create_tree_icon("./gui/icons/syncing.png", rowheight)
        self.icon_collection = self._create_tree_icon("./gui/icons/collection.png", rowheight)
        self.icon_notebook = self._create_tree_icon("./gui/icons/notebook.png", rowheight)
        self.icon_epub = self._create_tree_icon("./gui/icons/epub.png", rowheight)
        self.icon_pdf = self._create_tree_icon("./gui/icons/pdf.png", rowheight)
        self.icon_notebook_out_of_sync = self._create_tree_icon("./gui/icons/notebook_out_of_sync.png", rowheight)
        self.icon_epub_out_of_sync = self._create_tree_icon("./gui/icons/epub_out_of_sync.png", rowheight)
        self.icon_pdf_out_of_sync = self._create_tree_icon("./gui/icons/pdf_out_of_sync.png", rowheight)
        self.icon_weird = self._create_tree_icon("./gui/icons/weird.png", rowheight)

        # Context menu on right click
        # Check out drag and drop: https://stackoverflow.com/questions/44887576/how-can-i-create-a-drag-and-drop-interface
        self.tree.bind("<Button-3>", self.tree_right_click)
        self.context_menu =tk.Menu(root, tearoff=0, font=font_size)
        self.context_menu.add_command(label='Open with annotations', command=self.btn_open_click)
        self.context_menu.add_command(label='Open without annotations', command=self.btn_open_original_click)
        self.context_menu.add_command(label='Rename')
        self.context_menu.add_command(label='Delete', command=self.btn_delete_async_click)
        self.context_menu.add_separator()
        self.context_menu.add_command(label='Copy', command=self.btn_copy_async_click)
        self.context_menu.add_command(label='Paste', command=self.btn_paste_async_click)
        self.context_menu.add_command(label='Cut')
        self.context_menu.add_separator()
        self.context_menu.add_command(label='Sync local', command=self.btn_sync_async_click)
        self.context_menu.add_command(label='Delete local', command=self.btn_delete_local_click)

        self.tree.bind("<Double-1>", self.tree_double_click)

        # Footer
        self.lower_frame = tk.Frame(root)
        self.lower_frame.pack(side=tk.BOTTOM, anchor="w")

        btn = tk.Button(self.lower_frame, text="Sync local")
        btn.pack(side = tk.LEFT)

        btn = tk.Button(self.lower_frame, text="Delete local", command=self.btn_delete_local_all_click)
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
                item.parent.id, 
                pos, 
                item.id)
            self._update_tree_item(item)

            item.add_state_listener(self._update_tree_item)    

        for child in item.children:
            self._update_tree(child)



    #
    # EVENT HANDLER
    #
    def sign_in_event_handler(self, event, data):
        if event == api.remarkable_client.EVENT_SUCCESS:
            root = self.item_factory.get_root()
            self._update_tree(root)


    #
    # EVENT HANDLER
    #
    def tree_right_click(self, event):
        selected_ids = self.tree.selection()
        if selected_ids:
            items = [self.item_factory.get_item(id) for id in selected_ids]
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
        selected_ids = self.tree.selection()
        items = [self.item_factory.get_item(id) for id in selected_ids]
        
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
            
    
    def btn_delete_local_click(self):
        selected_ids = self.tree.selection()
        for id in selected_ids:
            self.item_factory.depth_search(
                fun = lambda item: item.delete_local(),
                item = self.item_factory.get_item(id)
        )


    def btn_sync_async_click(self):
        selected_ids = self.tree.selection()

        def sync(item):
            thread = threading.Thread(target=self._sync_and_open_item, args=(item, True))
            thread.start()

        for id in selected_ids:
            self.item_factory.depth_search(
                fun = sync,
                item = self.item_factory.get_item(id)
        )
    

    def _update_tree_item(self, item):
        if item.state == model.item.STATE_DELETED:
            self.tree.delete(item.id)
        else:
            icon = self._get_icon(item)
            self.tree.item(
                item.id, 
                image=icon, 
                text=" " + item.name,
                values=(item.local_modified_time(), item.current_page))

    def _get_icon(self, item):
        if not item.is_document:
            return self.icon_collection
        

        if item.state == model.document.STATE_NOT_SYNCED:
            return self.icon_cloud
        
        elif item.state == model.document.STATE_SYNCING:
            return self.icon_syncing

        if item.state == model.document.STATE_SYNCED:
            if item.type == model.document.TYPE_PDF:
                return self.icon_pdf
            elif item.type == model.document.TYPE_EPUB:
                return self.icon_epub
            else: 
                return self.icon_notebook

        if item.state == model.document.STATE_OUT_OF_SYNC:
            if item.type == model.document.TYPE_PDF:
                return self.icon_pdf_out_of_sync
            elif item.type == model.document.TYPE_EPUB:
                return self.icon_epub_out_of_sync
            else: 
                return self.icon_notebook_out_of_sync
        
        return self.icon_weird


    def _sync_and_open_item(self, item, force, open_file=False, open_original_file=False):   
        item.sync(force=force)

        if open_file:
            file_to_open = item.get_original_file() if open_original_file \
                    else item.get_annotated_or_original_file()
            subprocess.call(('xdg-open', file_to_open))


    def tree_double_click(self, event):
        selected_ids = self.tree.selection()
        item = self.item_factory.get_item(selected_ids[0])
        
        if item.is_document:
            self._open_selection_async()


    def key_binding_return(self, event):
        self.btn_open_click()


    def btn_open_click(self):
        self._open_selection_async()
    

    def btn_open_original_click(self):
        self._open_selection_async(open_original_file=True)


    def btn_delete_local_all_click(self):
        # Clean everything, also if some (old) things exist
        shutil.rmtree(utils.config.PATH, ignore_errors=True)
        Path(utils.config.PATH).mkdir(parents=True, exist_ok=True)

        self.item_factory.depth_search(
            fun=lambda item: item.update_state()
        )


    def _open_selection_async(self, open_original_file = False):
        selected_ids = self.tree.selection()

        def open_item(item):
            for child in item.children:
                open_item(child)
            
            if not item.is_document:
                return

            thread = threading.Thread(target=self._sync_and_open_item, args=(item, False, True, open_original_file))
            thread.start()

        for id in selected_ids:
            item = self.item_factory.get_item(id)
            open_item(item)

    #
    # Copy, Paste, Cut
    #
    def key_binding_paste(self, event):
        self.btn_paste_async_click()

    def btn_paste_async_click(self):
        selected_ids = self.tree.selection()

        if len(selected_ids) > 1:
            messagebox.showerror("Paste error", "Can paste only into one collection.")
            return
        
        elif len(selected_ids) == 1:
            item = self.item_factory.get_item(selected_ids[0])
            parent_id = str(item.parent.id if item.is_document else item.id)
        
        else:
            parent_id = ""      

        file_path = self.root.clipboard_get()
        if not os.path.exists(file_path):
            messagebox.showerror("Paste error", "No file found to upload.")
            return

        is_pdf = file_path.endswith(".pdf")
        is_epub = file_path.endswith(".epub")
        filetype = "pdf" if is_pdf else "epub" if is_epub else None

        if filetype is None:
            messagebox.showerror("Paste error", "Only .pdf and .epub files are supported.")
            return
        
        # Upload file
        id, metadata, mf = create_document_zip(
            file_path, 
            file_type=filetype, 
            parent_id = parent_id)
        metadata = self.rm_client.upload(id, metadata, mf)

        # Add to tree
        parent = self.item_factory.get_item(parent_id)
        item = self.item_factory.create_item(metadata, parent)
        self._update_tree(item)



    def key_binding_copy(self, event):
        self.btn_copy_async_click()


    def btn_copy_async_click(self):
        self.root.clipboard_clear()
        selected_ids = self.tree.selection()

        def sync_and_copy(item):
            self._sync_and_open_item(item, force=False)
            self.root.clipboard_append(item.path_annotated_pdf)

        def run():
            for id in selected_ids:
                self.item_factory.depth_search(
                    fun=lambda item: sync_and_copy(item),
                    item = self.item_factory.get_item(id))
        threading.Thread(target=run).start()
        self.root.update()
            