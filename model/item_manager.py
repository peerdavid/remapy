import os
import shutil
import json 

from api.remarkable_client import RemarkableClient
import model.item
from model.collection import Collection
from model.document import Document
from utils.helper import Singleton
import utils.config


class ItemManager(metaclass=Singleton):
    """ The ItemManager keeps track of all the collections and documents
        that are stored in your rm cloud. Load and create items through 
        this class. It is a singleton such that it is ensured that access to 
        items goes through the same tree structure.
    """
    

    def __init__(self,):
        self.rm_client = RemarkableClient()
        self.root = None


    def get_root(self, force=False):
        """ Get root node of tree from cache or download it from the rm cloud. 
            If you are offline, we load the stored tree from last time.
            Note that if we are online we sync all files with the rm cloud 
            i.e. delete old local files.
        """
        if not self.root is None and not force:
            return self.root

        entries, is_online = self._get_entries()
        
        self._clean_local_items(entries)
        self.root = self._create_tree(entries)
        return self.root, is_online


    def get_item(self, id, item=None):
        self.get_root()
        
        item = self.root if item is None else item

        if item.id == id:
            return item
        
        for child in item.children:
            found = self.get_item(id, child)
            if found != None:
                return found
        
        return None


    def create_backup(self, backup_path):
        # Create folder structure
        self.traverse_tree(
            fun=lambda item: item.create_backup(backup_path),
            document=False,
            collection=True)

        # And copy files into it
        self.traverse_tree(
            fun=lambda item: item.create_backup(backup_path),
            document=True,
            collection=False)


    def traverse_tree(self, fun, item=None, document=True, collection=True):
        item = self.get_root() if item == None else item
        
        for child in item.children:
            self.traverse_tree(fun, child, document, collection)
        
        if item.is_document and document or item.is_collection and collection:
            fun(item)


    def create_item(self, entry, parent):
        if entry["Type"] == "CollectionType":
            new_object = Collection(entry, parent)

        elif entry["Type"] == "DocumentType":
            new_object = Document(entry, parent)

        else: 
            raise Exception("Unknown type %s" % entry["Type"])
        
        parent.add_child(new_object)
        return new_object

        
    def _get_entries(self):
        try:
            entries = self.rm_client.list_items()
            return entries, entries != None
        except:
            entries = []
            for local_id in os.listdir(utils.config.PATH):
                entry_path = model.item.get_path_metadata_local(local_id)
                with open(entry_path, 'r') as file:
                    entry_content = file.read().replace('\n', '')
                
                entry = json.loads(entry_content)
                entries.append(entry)

        return entries, False


    def _clean_local_items(self, entries):
        online_ids = [entry["ID"] for entry in entries]
        for local_id in os.listdir(utils.config.PATH):
            if local_id in online_ids:
                continue
            
            local_file_or_folder = "%s/%s" % (utils.config.PATH, local_id)
            if os.path.isfile(local_file_or_folder):
                os.remove(local_file_or_folder)
            else:
                shutil.rmtree(local_file_or_folder)
            print("Deleted local item %s" % local_id)


    def _create_tree(self, entries):

        lookup_table = {}
        for i in range(len(entries)):
            lookup_table[entries[i]["ID"]] = i

        # Create a dummy root object where everything starts with parent 
        # "". This parent "" should not be changed as it is also used in 
        # the rm cloud
        root = Collection(None, None)
        items = {
            "": root
        }

        # We do this for every element, because _create_item_and_parents
        # only ensures that all parents already exist
        for i in range(len(entries)):
            self._create_item_and_parents(i, entries, items, lookup_table)

        return root


    def _create_item_and_parents(self, i, entries, items, lookup_table):
        entry = entries[i]
        parent_id = entry["Parent"]

        if i < 0 or len(entries) <= 0 or entry["ID"] in items:
            return

        if not parent_id in items:
            if not parent_id in lookup_table:
                print("(Warning) No parent for item %s" % entry["VissibleName"])
                parent_id = ""
            else:
                parent_pos = lookup_table[parent_id]
                self._create_item_and_parents(parent_pos, entries, items, lookup_table)

        parent = items[parent_id]
        new_object = self.create_item(entry, parent)
        items[new_object.id] = new_object
