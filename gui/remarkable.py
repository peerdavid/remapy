import os
import subprocess
import threading
import shutil
import queue
from time import gmtime, strftime
import numpy as np
from pathlib import Path
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from PIL import ImageTk as itk
from PIL import Image

import api.remarkable_client
from api.remarkable_client import RemarkableClient
from model.item_manager import ItemManager
from model.item import Item
import model.document
from model.document import Document, create_document_zip
import utils.config

class Remarkable(object):

    #
    # CTOR
    #
    def __init__(self, root, window, font_size=14, rowheight=14):
        
        self.root = root
        app_dir = os.path.dirname(__file__)
        icon_dir = os.path.join(app_dir, 'icons/')

        # Create tkinter elements
        self.nodes = dict()
        self.rm_client = RemarkableClient()
        self.item_manager = ItemManager()

        self.tree_style = ttk.Style()
        self.tree_style.configure("remapy.style.Treeview", highlightthickness=0, bd=0, font=font_size, rowheight=rowheight)
        self.tree_style.configure("remapy.style.Treeview.Heading", font=font_size)
        self.tree_style.layout("remapy.style.Treeview", [('remapy.style.Treeview.treearea', {'sticky': 'nswe'})])
        
        self.upper_frame = tk.Frame(root)
        self.upper_frame.pack(expand=True, fill=tk.BOTH)

        self.label_offline = tk.Label(window, fg="#f44336", font='Arial 13 bold')
        self.label_offline.place(relx=1.0, y=12, anchor="e")


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
        
        self.icon_cloud = self._create_tree_icon(icon_dir + "cloud.png", rowheight)
        self.icon_document_syncing = self._create_tree_icon(icon_dir + "document_syncing.png", rowheight)
        self.icon_document_upload = self._create_tree_icon(icon_dir + "document_upload.png", rowheight)
        self.icon_collection_syncing = self._create_tree_icon(icon_dir + "collection_syncing.png", rowheight)
        self.icon_collection = self._create_tree_icon(icon_dir + "collection.png", rowheight)
        self.icon_notebook = self._create_tree_icon(icon_dir + "notebook.png", rowheight)
        self.icon_epub = self._create_tree_icon(icon_dir + "epub.png", rowheight)
        self.icon_pdf = self._create_tree_icon(icon_dir + "pdf.png", rowheight)
        self.icon_notebook_out_of_sync = self._create_tree_icon(icon_dir + "notebook_out_of_sync.png", rowheight)
        self.icon_epub_out_of_sync = self._create_tree_icon(icon_dir + "epub_out_of_sync.png", rowheight)
        self.icon_pdf_out_of_sync = self._create_tree_icon(icon_dir + "pdf_out_of_sync.png", rowheight)
        self.icon_weird = self._create_tree_icon(icon_dir + "weird.png", rowheight)

        # Context menu on right click
        # Check out drag and drop: https://stackoverflow.com/questions/44887576/how-can-i-create-a-drag-and-drop-interface
        self.tree.bind("<Button-3>", self.tree_right_click)
        self.context_menu =tk.Menu(root, tearoff=0, font=font_size)
        self.context_menu.add_command(label='Open with annotations', command=self.btn_open_item_click)
        self.context_menu.add_command(label='Open without annotations', command=self.btn_open_item_original_click)
        self.context_menu.add_command(label='Open in file explorer', command=self.btn_open_in_file_explorer)
        self.context_menu.add_separator()
        self.context_menu.add_command(label='ReSync', command=self.btn_resync_item_click)
        self.context_menu.add_command(label='Rename')
        self.context_menu.add_command(label='Delete', command=self.btn_delete_item_click)
        self.context_menu.add_separator()
        self.context_menu.add_command(label='Copy', command=self.btn_copy_async_click)
        self.context_menu.add_command(label='Paste', command=self.btn_paste_async_click)
        self.context_menu.add_command(label='Cut')   

        self.tree.bind("<Double-1>", self.tree_double_click)

        # Footer
        self.lower_frame = tk.Frame(root)
        self.lower_frame.pack(side=tk.BOTTOM, anchor="w", fill=tk.X)

        self.lower_frame_left = tk.Frame(self.lower_frame)
        self.lower_frame_left.pack(side=tk.LEFT)

        self.btn_sync = tk.Button(self.lower_frame_left, text="Sync", width=10, command=self.btn_sync_click)
        self.btn_sync.pack(anchor="w")

        self.btn_resync = tk.Button(self.lower_frame_left, text="ReSync", width=10, command=self.btn_resync_click)
        self.btn_resync.pack(anchor="w")

        self.lower_frame_right = tk.Frame(self.lower_frame)
        self.lower_frame_right.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.log_widget = tk.scrolledtext.ScrolledText(self.lower_frame_right, height=3)
        self.log_widget.insert(tk.END, "RemaPy Explorer v0.1")
        self.log_widget.config(state=tk.DISABLED)
        self.log_widget.pack(expand=True, fill=tk.X)
        
        self.rm_client.listen_sign_in(self)
    

    def _set_online_mode(self, mode):
        self.btn_sync.config(state=mode)
        self.btn_resync.config(state=mode)
        self.context_menu.entryconfig(4, state=mode)
        self.context_menu.entryconfig(5, state=mode)
        self.context_menu.entryconfig(6, state=mode)
        self.context_menu.entryconfig(8, state=mode)
        self.context_menu.entryconfig(9, state=mode)
        self.context_menu.entryconfig(10, state=mode)

        bg = "#ffffff" if mode == "normal" else "#bdbdbd"
        self.tree_style.configure("remapy.style.Treeview", background=bg)

        if mode == "normal":
            self.label_offline.config(text="")
        else:
            self.label_offline.config(text="You are offline  ")

    def log(self, text):
        now = strftime("%H:%M:%S", gmtime())
        self.log_widget.config(state=tk.NORMAL)
        self.log_widget.insert(tk.END, "\n[%s] %s" % (str(now), text))
        self.log_widget.config(state=tk.DISABLED)
        self.log_widget.see(tk.END)

    #
    # Tree
    #
    def _create_tree_icon(self, path, row_height):
        icon = Image.open(path)
        icon = icon.resize((row_height-4, row_height-4))
        return itk.PhotoImage(icon)


    def sign_in_event_handler(self, event, data):
        # Also if the login failed (e.g. we are offline) we try again 
        # if we can sync the items (e.g. with old user key) and otherwise 
        # we switch to the offline mode
        self.btn_sync_click()

    
    def _update_tree(self, item):
        if not item.is_root_item():
            tree_id = self.tree.insert(
                item.parent.id, 
                0, 
                item.id)
            
            self._update_tree_item(item)

            item.add_state_listener(self._update_tree_item)    

        # Sort by name and item type
        sorted_children = item.children
        sorted_children.sort(key=lambda x: str.lower(x.name), reverse=True)
        sorted_children.sort(key=lambda x: int(x.is_document), reverse=True)
        for child in sorted_children:
            self._update_tree(child)

    
    def tree_right_click(self, event):
        selected_ids = self.tree.selection()
        if selected_ids:
            items = [self.item_manager.get_item(id) for id in selected_ids]
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
            if item.state == model.item.STATE_SYNCED:
                return self.icon_collection
            else:
                return self.icon_collection_syncing
        

        if item.state == model.document.STATE_NOT_SYNCED:
            return self.icon_cloud
        
        elif item.state == model.item.STATE_SYNCING:
            return self.icon_document_syncing

        if item.state == model.item.STATE_SYNCED:
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


    #
    # SYNC AND OPEN
    #
    def btn_resync_item_click(self):
        self._sync_selection_async(
                force=True, 
                open_file=False, 
                open_original=False)


    def tree_double_click(self, event):
        selected_ids = self.tree.selection()
        item = self.item_manager.get_item(selected_ids[0])
        
        if item.is_document:
            self._sync_selection_async(
                force=False, 
                open_file=True, 
                open_original=False)


    def key_binding_return(self, event):
        self.btn_open_item_click()


    def btn_open_item_click(self):
        self._sync_selection_async(
                force=False, 
                open_file=True, 
                open_original=False)
    

    def btn_open_item_original_click(self):
        self._sync_selection_async(
                force=False, 
                open_file=True, 
                open_original=True)


    def btn_resync_click(self):

        if self.is_online:
            message = "Do you really want to delete ALL local files and download ALL documents again?"
        else:
            message = "Do you really want resync without a connection to the remarkable cloud?"
        
        result = messagebox.askquestion("Warning", message, icon='warning')

        if result != "yes":
            return 

        # Clean everything, also if some (old) things exist
        shutil.rmtree(utils.config.PATH, ignore_errors=True)
        Path(utils.config.PATH).mkdir(parents=True, exist_ok=True)

        self.item_manager.traverse_tree(
            fun=lambda item: item.update_state()
        )

        # And sync again
        self.btn_sync_click()


    def btn_sync_click(self):
        self.log("Syncing all documents...")
        root, self.is_online = self.item_manager.get_root(force=True)

        if self.is_online:
            self._set_online_mode("normal")
        else:
            self.log("OFFLINE MODE: No connection to the remarkable cloud")
            self._set_online_mode("disabled")

        self.tree.delete(*self.tree.get_children())
        self._update_tree(root)

        self._sync_items_async([self.item_manager.get_root()],
                force=False, 
                open_file=False, 
                open_original=False)


    def _sync_selection_async(self, force=False, open_file=False, open_original=False):
        selected_ids = self.tree.selection()
        items = [self.item_manager.get_item(id) for id in selected_ids]
        self._sync_items_async(items, force, open_file, open_original)


    def _sync_items_async(self, items, force=False, open_file=False, open_original=False):
        """ To keep the gui responsive...
        """
        thread = threading.Thread(target=self._sync_items, args=(items, force, open_file, open_original))
        thread.start()


    def _sync_items(self, items, force=False, open_file=False, open_original=False):
        q = queue.Queue()
        threads = []

        def worker():
            while True:
                item = q.get()
                if item is None:
                    break
                
                try:
                    self._sync_and_open_item(item, force, open_file, open_original)
                except Exception as e:
                    if open_file:
                        self.log("(Error) Could not open '%s'" % item.name[0:50])
                    else:
                        self.log("(Error) Could not sync '%s'" % item.name[0:50])
                    print(e)
                    
                q.task_done()

        num_worker_threads = 10
        for i in range(num_worker_threads):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)
        
        # Add all items and child items
        for item in items:
            self.item_manager.traverse_tree(fun=q.put, item = item)
            
        q.join()

        # stop workers
        for i in range(num_worker_threads):
            q.put(None)
        for t in threads:
            t.join()
    
        

    def _sync_and_open_item(self, item, force=False, open_file=False, open_original=False):   

        if (force or item.state != model.item.STATE_SYNCED) and not item.is_root_item():
            item.sync()

            if item.is_document:
                self.log("Synced '%s'" %  item.full_name())

        if open_file and item.is_document:
            file_to_open = item.get_original_file() if open_original \
                    else item.get_annotated_or_original_file()

            if file_to_open.endswith(".pdf"):
                subprocess.call(["evince", "-p", str(item.current_page), file_to_open])
            else:
                subprocess.call(["xdg-open", file_to_open])


    #
    # Delete
    #
    def key_binding_delete(self, event):
        self.btn_delete_item_click()


    def btn_delete_item_click(self):
        selected_ids = self.tree.selection()
        items = [self.item_manager.get_item(id) for id in selected_ids]
        
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
                self.log("Deleted %s" % item.full_name())
        threading.Thread(target=run).start()


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
            item = self.item_manager.get_item(selected_ids[0])
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
        
        def run():
            # ToDo: Refactor this function into the item manager where a 
            #       callback indicates the state...
            # Upload file
            id, metadata, mf = create_document_zip(
                file_path, 
                file_type=filetype, 
                parent_id = parent_id)

            # Show in tree
            self.tree.insert(
                parent_id, 
                1000, 
                id,
                text= " " + metadata["VissibleName"],
                image=self.icon_document_upload)

            # Upload file into cloud
            metadata = self.rm_client.upload(id, metadata, mf)

            # Add to tree
            parent = self.item_manager.get_item(parent_id)
            item = self.item_manager.create_item(metadata, parent)
            item.add_state_listener(self._update_tree_item)

            # Download again to get it correctly
            item.sync()
            self.log("Successfully uploaded %s" % item.full_name())

        
        self.log("Uploading %s..." % file_path)
        threading.Thread(target=run).start()


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
                self.item_manager.traverse_tree(
                    fun=lambda item: sync_and_copy(item),
                    item = self.item_manager.get_item(id))
        threading.Thread(target=run).start()
        self.root.update()


    def btn_open_in_file_explorer(self):
        selected_ids = self.tree.selection()
        items = [self.item_manager.get_item(id) for id in selected_ids]

        for item in items:
            if not item.is_document:
                continue

            subprocess.call(('xdg-open', item.path_remapy))
