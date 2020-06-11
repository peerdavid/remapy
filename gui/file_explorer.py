import os
import subprocess
import threading
import shutil
import queue
import uuid
from time import gmtime, strftime
import datetime
import numpy as np
from pathlib import Path
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from tkinter import simpledialog
from PIL import ImageTk as itk
from PIL import Image

from gui.elements.entry_with_placeholder import EntryWithPlaceholder
import api.remarkable_client
from api.remarkable_client import RemarkableClient
from model.item_manager import ItemManager
from model.item import Item
import model.document
from model.document import Document
import utils.config


class FileExplorer(object):
    """ Main window of RemaPy which displays the tree structure of
        all your rm documents and collections.
    """

    def __init__(self, root, window, font_size=14, row_height=14):
        
        self.root = root
        self.window = window
        self.app_dir = os.path.dirname(__file__)
        self.icon_dir = os.path.join(self.app_dir, 'icons/')
        self._cached_icons = {}
        self._icon_lock = threading.Lock()
        self.row_height = row_height

        # Create tkinter elements
        self.nodes = dict()
        self.rm_client = RemarkableClient()
        self.item_manager = ItemManager()

        self.tree_style = ttk.Style()
        self.tree_style.configure("remapy.style.Treeview", highlightthickness=0, bd=0, font=font_size, rowheight=row_height)
        self.tree_style.configure("remapy.style.Treeview.Heading", font=font_size)
        self.tree_style.layout("remapy.style.Treeview", [('remapy.style.Treeview.treearea', {'sticky': 'nswe'})])
        
        self.upper_frame = tk.Frame(root)
        self.upper_frame.pack(expand=True, fill=tk.BOTH)

        self.label_offline = tk.Label(window, fg="#f44336", font='Arial 13 bold')
        self.label_offline.place(relx=0.5, y=12, anchor="center")

        self.entry_filter = None
        self.entry_filter_var = tk.StringVar()
        self.entry_filter_var.trace("w", self.filter_changed_event_handler)
        self.entry_filter = EntryWithPlaceholder(window, "Filter...", textvariable=self.entry_filter_var)
        self.entry_filter.place(relx=1.0, y=12, anchor="e")

        # Add tree and scrollbars
        self.tree = ttk.Treeview(self.upper_frame, style="remapy.style.Treeview")
        self.tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.tree.bind("<FocusOut>", self.tree_focus_out_event_handler)
        self.tree.bind("<FocusIn>", self.tree_focus_in_event_handler)
        
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
        self.tree.focus_set()

        self.window.bind("<Escape>", self.key_binding_escape)
        
        # Context menu on right click
        # Check out drag and drop: https://stackoverflow.com/questions/44887576/how-can-i-create-a-drag-and-drop-interface
        self.tree.bind("<Button-3>", self.tree_right_click)
        self.context_menu =tk.Menu(root, tearoff=0, font=font_size)
        self.context_menu.add_command(label='Open <Return>', command=self.btn_open_item_click)
        self.context_menu.add_command(label='Open only annotated pages', command=self.btn_open_oap_item_click)
        self.context_menu.add_command(label='Open without annotations', command=self.btn_open_item_original_click)
        self.context_menu.add_command(label='Open folder', command=self.btn_open_in_file_explorer)
        self.context_menu.add_separator()
        self.context_menu.add_command(label='ReSync <F5>', command=self.btn_resync_item_click)
        self.context_menu.add_command(label='Toggle bookmark <Ctrl+b>', command=self.btn_toggle_bookmark)
        self.context_menu.add_command(label='Rename <F2>', command=self.btn_rename_item_click)
        self.context_menu.add_command(label='Delete <Del>', command=self.btn_delete_item_click)
        self.context_menu.add_separator()
        self.context_menu.add_command(label='Paste <Ctrl+v>', command=self.btn_paste_async_click)
        

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
        
        self.rm_client.listen_sign_in_event(self)
    

    def _set_online_mode(self, mode):
        self.btn_sync.config(state=mode)
        self.btn_resync.config(state=mode)
        self.context_menu.entryconfig(5, state=mode)
        self.context_menu.entryconfig(6, state=mode)
        self.context_menu.entryconfig(7, state=mode)
        self.context_menu.entryconfig(8, state=mode)
        self.context_menu.entryconfig(10, state=mode)

        bg = "#ffffff" if mode == "normal" else "#bdbdbd"
        self.tree_style.configure("remapy.style.Treeview", background=bg)

        if mode == "normal":
            self.label_offline.config(text="")
        else:
            self.label_offline.config(text="Offline")


    def log_console(self, text):
        now = strftime("%H:%M:%S", gmtime())
        self.log_widget.config(state=tk.NORMAL)
        self.log_widget.insert(tk.END, "\n[%s] %s" % (str(now), text))
        self.log_widget.config(state=tk.DISABLED)
        self.log_widget.see(tk.END)
    
    #
    # Tree
    #
    def tree_focus_out_event_handler(self, *args):
        self.window.unbind("<Control-v>")
        self.window.unbind("<Return>")
        self.window.unbind("<Delete>")
        self.window.unbind("<Control-f>")
        self.window.unbind("<Control-b>")
        self.window.unbind("<F5>")
        self.window.unbind("<F2>")
    

    def tree_focus_in_event_handler(self, *args):
        self.window.bind("<Control-f>", self.key_binding_filter)
        self.window.bind("<Control-v>", self.key_binding_paste)
        self.window.bind("<Control-b>", self.key_binding_toggle_bookmark)
        self.window.bind("<F5>", self.key_binding_resync)
        self.window.bind("<Return>", self.key_binding_return)
        self.window.bind("<Delete>", self.key_binding_delete)
        self.window.bind("<F2>", self.key_binding_rename)


    def sign_in_event_handler(self, event, data):
        # Also if the login failed (e.g. we are offline) we try again 
        # if we can sync the items (e.g. with old user key) and otherwise 
        # we switch to the offline mode
        if event == api.remarkable_client.EVENT_SUCCESS or event == api.remarkable_client.EVENT_USER_TOKEN_FAILED:
            self.btn_sync_click()


    def key_binding_filter(self, event):
        self.entry_filter.focus_set()
    

    def key_binding_escape(self, event):
        self.tree.focus_set()
        children = self.tree.get_children()
        if len(children) > 0:
            self.tree.focus(children[0])
        else:
            self.tree.focus()
            

    def filter_changed_event_handler(self, placeholder, *args):
        if self.entry_filter is None:
            return 

        filter_text = self.entry_filter_var.get()
        if filter_text == self.entry_filter.placeholder:
            filter_text = None
        
        root = self.item_manager.get_root()
        self.tree.delete(*self.tree.get_children())
        self._update_tree(root, filter_text)


    def _update_tree(self, item, filter=None):
        try:
            is_direct_match = False
            if not item.is_root():
                is_match, is_direct_match = self._match_filter(item, filter)
                if is_match:
                    self.tree.insert(
                        item.parent().id(), 
                        0, 
                        item.id(),
                        open=filter!=None)

                    self._update_tree_item(item)
                    item.add_state_listener(self._update_tree_item)
                    include_all_childs = item.is_collection() and is_direct_match
                    if include_all_childs:
                        filter = None

            # Sort by name and item type
            sorted_children = item.children()
            sorted_children.sort(key=lambda x: str.lower(x.name()), reverse=True)
            sorted_children.sort(key=lambda x: int(x.is_document()), reverse=True)
            for child in sorted_children:
                self._update_tree(child, filter)
        except Exception as e:
            print("(Warning) Failed to add item %s" % item.id())
            print(e)
            # Try to remove wrong item from tree
            try:
                self.tree.delete(item.id())
            except:
                pass
    

    def _match_filter(self, item, filter):  
        """ Returns whether we have a match on this path (to include all 
            parent folders) and whether the given item was the matching one.
        """
        if filter is None or filter == "":
            return True, True
        
        if filter.startswith("!b "):
            bookmarked_only = True
            text_filter = filter[3:]
        elif filter == "!b":
            bookmarked_only = True
            text_filter = ""
        else:
            bookmarked_only = False
            text_filter = filter

        is_match = (text_filter.lower() in item.name().lower())
        
        if bookmarked_only:
            is_match = is_match and item.bookmarked()

        if is_match:
            return is_match, True

        for child in item.children():
            child_match, _ = self._match_filter(child, filter)
            if child_match:
                return child_match, False

        return False, False
    

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
            self.tree.delete(item.id())
        else:
            icon = self._get_icon(item)
            self.tree.item(
                item.id(), 
                image=icon, 
                text=" " + item.name(),
                values=(
                    item.modified_time().strftime("%Y-%m-%d %H:%M:%S"), 
                    item.current_page()))


    def _get_icon(self, item):
        if item.is_collection():
            if item.state == model.item.STATE_SYNCED:
                return self._create_tree_icon("collection", item.bookmarked())
            else:
                return self._create_tree_icon("collection_syncing")
        

        if item.state == model.document.STATE_NOT_SYNCED:
            return self._create_tree_icon("cloud")
        
        elif item.state == model.item.STATE_SYNCING:
            return self._create_tree_icon("document_syncing")

        if item.state == model.item.STATE_SYNCED:
            if item.type == model.document.TYPE_PDF:
                return self._create_tree_icon("pdf", item.bookmarked())
            elif item.type == model.document.TYPE_EPUB:
                return self._create_tree_icon("epub", item.bookmarked())
            else: 
                return self._create_tree_icon("notebook", item.bookmarked())

        if item.state == model.document.STATE_OUT_OF_SYNC:
            if item.type == model.document.TYPE_PDF:
                return self._create_tree_icon("pdf_out_of_sync")
            elif item.type == model.document.TYPE_EPUB:
                return self._create_tree_icon("epub_out_of_sync")
            else: 
                return self._create_tree_icon("notebook_out_of_sync")
        
        return self._create_tree_icon("weird")

    
    def _create_tree_icon(self, name, bookmarked=False):
        key = "%s_%s" % (name, bookmarked)
        if key in self._cached_icons:
                return self._cached_icons[key]

        # If possible return icon from cache
        with self._icon_lock:

            # Double check if key is in cached icons
            if key in self._cached_icons:
                return self._cached_icons[key]
        
            icon_size = self.row_height-4
            path = "%s%s.png" % (self.icon_dir, name)
            icon = Image.open(path)
            icon = icon.resize((icon_size, icon_size))

            if bookmarked:
                icon_star = Image.open("%s%s.png" % (self.icon_dir, "star"))
                icon_star = icon_star.resize((icon_size, icon_size))
                icon.paste(icon_star, None, icon_star)
            
            self._cached_icons[key] = itk.PhotoImage(icon)
            return self._cached_icons[key]


    def key_binding_rename(self, event):
        self.btn_rename_item_click()


    def btn_rename_item_click(self):
        selected_ids = self.tree.selection()
        if len(selected_ids) != 1:
            messagebox.showerror("Error", "Select exactly one item to rename.", icon='error')
            return
        
        item = self.item_manager.get_item(selected_ids[0])

        if item.name() == "Quick sheets" and item.parent().is_root():
            messagebox.showerror("Error", "You can not rename the Quick sheets.", icon='error')
            return

        name = simpledialog.askstring('Rename', 'Enter new name', initialvalue=item.name())
        if name is None:
            return

        item.rename(name)

    def key_binding_resync(self, event):
        self.btn_resync_item_click()

    def btn_resync_item_click(self):
        self._sync_selection_async(
                force=True, 
                open_file=False, 
                open_original=False)


    def tree_double_click(self, event):
        selected_ids = self.tree.selection()
        item = self.item_manager.get_item(selected_ids[0])
        
        if item.is_document():
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
    

    def btn_open_oap_item_click(self):
        self._sync_selection_async(
                        force=False, 
                        open_file=True, 
                        open_oap=True)


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
        self.log_console("Syncing all documents...")
        root, self.is_online = self.item_manager.get_root(force=True)

        if self.is_online:
            self._set_online_mode("normal")
        else:
            self.log_console("OFFLINE MODE: No connection to the remarkable cloud")
            self._set_online_mode("disabled")

        self.tree.delete(*self.tree.get_children())
        self._update_tree(root)

        self._sync_items_async([self.item_manager.get_root()],
                force=False, 
                open_file=False, 
                open_original=False,
                open_oap=False)


    def _sync_selection_async(self, force=False, open_file=False, open_original=False, open_oap=False):
        selected_ids = self.tree.selection()
        items = [self.item_manager.get_item(id) for id in selected_ids]
        self._sync_items_async(items, force, open_file, open_original, open_oap)


    def _sync_items_async(self, items, force, open_file, open_original, open_oap):
        """ To keep the gui responsive...
        """
        thread = threading.Thread(target=self._sync_items, args=(items, force, open_file, open_original, open_oap))
        thread.start()


    def _sync_items(self, items, force, open_file, open_original, open_oap):
        q = queue.Queue()
        threads = []

        def worker():
            while True:
                item = q.get()
                if item is None:
                    break
                
                try:
                    self._sync_and_open_item(item, force, open_file, open_original, open_oap)
                except Exception as e:
                    if open_file:
                        self.log_console("(Error) Could not open '%s'" % item.name())
                    else:
                        self.log_console("(Error) Could not sync '%s'" % item.name())
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
    

    def _sync_and_open_item(self, item, force, open_file, open_original, open_oap):   
        
        if item.state == model.item.STATE_SYNCING:
            self.log_console("Already syncing '%s'" %  item.full_name())
            return

        if (force or item.state != model.item.STATE_SYNCED) and not item.is_root():
            item.sync()

            if item.is_document():
                self.log_console("Synced '%s'" %  item.full_name())

        if open_file and item.is_document():
            if open_original:
                file_to_open = item.orig_file()
            elif open_oap:
                file_to_open = item.oap_file()
                if file_to_open == None:
                    messagebox.showinfo("Information", "Document is not annotated.", icon='info')
                    return
            else: 
                file_to_open = item.ann_or_orig_file()

            if file_to_open.endswith(".pdf"):
                try:
                    current_page = 0 if open_oap else item.current_page()
                    subprocess.call(["evince", "-i", str(current_page), file_to_open])
                except:
                    subprocess.call(["xdg-open", file_to_open])    
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
            if item.is_document():
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
                if item.name() == "Quick sheets" and item.parent().is_root():
                    self.log_console("(Warning) You can not delete the Quick sheets.")
                    continue

                item.delete()
                self.log_console("Deleted %s" % item.full_name())
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
            parent_id = str(item.parent().id() if item.is_document() else item.id())
        
        else:
            parent_id = ""      
    
        def is_file(path):
            if not os.path.exists(path):
                return None
            elif path.endswith(".pdf"):
                return "pdf"
            elif path.endswith(".epub"):
                return "epub"
            return None            
        
        def is_url(url):
            return url.startswith("http")

        # Some versions of nautilus include "x-special/nautilus-clipboard file://..." 
        # Or dolphin simple adds "file://..."
        # See also issue #11
        print("Clipboard: " + str(self.root.clipboard_get()))
        paths = self.root.clipboard_get().split("\n")
        print("Paths 1: " + str(paths))
        paths = [path.replace("file://", "") for path in paths]
        print("Paths 2: " + str(paths))
        paths = list(filter(lambda path: is_file(path) != None or is_url(path), paths))
        print("Paths 3: " + str(paths))

        if len(paths) <= 0:
            messagebox.showerror(
                        "Failed to copy from clipboard", 
                        "The given clipboard is invalid. Only .pdf, .epub and urls are supported.\n\n%s" % self.root.clipboard_get())
            return
       
        def run(clipboard):       
            id = str(uuid.uuid4())         
            filetype = is_file(clipboard)
            if filetype != None:
                name = os.path.splitext(os.path.basename(clipboard))[0]
                self.tree.insert(
                    parent_id, 9999, id,
                    text= " " + name,
                    image=self._create_tree_icon("document_upload"))

                with open(clipboard, "rb") as f:
                    data = f.read()

            elif is_url(path):
                try:
                    import pdfkit
                    self.log_console("Converting webpage '%s'. This could take a few minutes." % clipboard)
                    name = clipboard
                    self.tree.insert(
                        parent_id, 9999, id,
                        text= " " + name,
                        image=self._create_tree_icon("document_upload"))

                    options = {
                        # Here we can manually set some cookies to 
                        # for example automatically accept terms of usage etc.
                        'cookie': [
                            ('DSGVO_ZUSAGE_V1', 'true')
                        ]
                    }
                    data = pdfkit.from_url(clipboard, False, options=options)
                    filetype = "pdf"
                except Exception as e:
                    messagebox.showerror(
                        "Failed to convert html to pdf", 
                        "Please ensure that you installed pdfkit and wkhtmltopdf correctly https://pypi.org/project/pdfkit/")
                    self.tree.delete(id)
                    return

            # Show new item in tree
            self.log_console("Upload document %s..." % name)

            # Upload
            item = self.item_manager.upload_file(
                id, parent_id, name, 
                filetype, data,
                self._update_tree_item)
            self.log_console("Successfully uploaded %s" % item.full_name())

        for path in paths:
            threading.Thread(target=run, args=[path]).start()


    def btn_open_in_file_explorer(self):
        selected_ids = self.tree.selection()
        items = [self.item_manager.get_item(id) for id in selected_ids]

        for item in items:
            if item.is_collection():
                continue

            subprocess.call(('xdg-open', item.path_remapy))
    
    def key_binding_toggle_bookmark(self, event):
        self.btn_toggle_bookmark()
        
    def btn_toggle_bookmark(self):
        selected_ids = self.tree.selection()
        items = [self.item_manager.get_item(id) for id in selected_ids]

        def run():
            for item in items:
                item.set_bookmarked(not item.bookmarked())
        threading.Thread(target=run).start()
