from api.client import Client
from api.object.collection import Collection
from api.object.document import Document
from api.helper import Singleton

class ItemFactory(metaclass=Singleton):
    

    def __init__(self,):
        self.rm_client = Client()
        self.root = None


    def get_item(self, uuid):
        if self.root is None:
            self.get_root()

        return self._get_item_rec(self.root, uuid)
        

    def _get_item_rec(self, item, uuid):
        if item.uuid == uuid:
            return item
        
        for child in item.children:
            found = self._get_item_rec(child, uuid)
            if found != None:
                return found

        return None


    def get_root(self):
        entries = self.rm_client.list_metadata()
        self.root = self._create_tree(entries)
        return self.root


    def _create_tree(self, entries):

        lookup_table = {}
        for i in range(len(entries)):
            lookup_table[entries[i]["ID"]] = i

        # Create a dummy root object where everything starts
        root = Collection(None, None)
        items = {
            "": root
        }

        for i in range(len(entries)):
            self._create_tree_recursive(i, entries, items, lookup_table)

        return root


    def _create_tree_recursive(self, i, entries, items, lookup_table):
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
                self._create_tree_recursive(parent_id, entries, items, lookup_table)

        parent = items[parent_uuid]
        new_object = self._item_factory(entry, parent)
        items[new_object.uuid] = new_object
            

    def _item_factory(self, entry, parent):
        if entry["Type"] == "CollectionType":
            new_object = Collection(entry, parent)

        elif entry["Type"] == "DocumentType":
            new_object = Document(entry, parent)

        else: 
            raise Exception("Unknown type %s" % entry["Type"])
        
        parent.add_child(new_object)
        return new_object
