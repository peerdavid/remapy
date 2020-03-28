from api.remarkable_client import RemarkableClient
from model.collection import Collection
from model.document import Document
from utils.helper import Singleton

class ItemFactory(metaclass=Singleton):
    
    def __init__(self,):
        self.rm_client = RemarkableClient()
        self.root = None


    def get_item(self, uuid, item=None):
        if self.root is None:
            self.get_root()
        
        item = self.root if item is None else item

        if item.uuid == uuid:
            return item
        
        for child in item.children:
            found = self.get_item(uuid, child)
            if found != None:
                return found
        
        return None


    def get_root(self):
        entries = self.rm_client.list_items()
        self.root = self._create_tree(entries)
        return self.root


    def depth_search(self, fun, item=None, document_only=True, collection_only=False):
        item = self.root if item == None else item
        
        for child in item.children:
            self.depth_search(fun, child)
        
        if collection_only and item.is_document:
            return
        
        if document_only and not item.is_document:
            return

        fun(item)


    def _create_tree(self, entries):

        lookup_table = {}
        for i in range(len(entries)):
            lookup_table[entries[i]["ID"]] = i

        # Create a dummy root object where everything starts
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
        parent_uuid = entry["Parent"]

        if i < 0 or len(entries) <= 0 or entry["ID"] in items:
            return

        if not parent_uuid in items:
            if not parent_uuid in lookup_table:
                print("(Warning) No parent for item %s" % entry["VissibleName"])
                parent_uuid = ""
            else:
                parent_id = lookup_table[parent_uuid]
                self._create_item_and_parents(parent_id, entries, items, lookup_table)

        parent = items[parent_uuid]
        new_object = self.create_item(entry, parent)
        items[new_object.uuid] = new_object
            

    def create_item(self, entry, parent):
        if entry["Type"] == "CollectionType":
            new_object = Collection(entry, parent)

        elif entry["Type"] == "DocumentType":
            new_object = Document(entry, parent)

        else: 
            raise Exception("Unknown type %s" % entry["Type"])
        
        parent.add_child(new_object)
        return new_object
