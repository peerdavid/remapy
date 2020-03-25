import os
from datetime import datetime


#
# OBJECTS
# See also https://github.com/splitbrain/ReMarkableAPI/wiki/Storage
#

class Item(object):

    def __init__(self, entry, parent=None):
        self.children = []

        is_root = entry is None
        if is_root:
            self.uuid = ""
            self.is_document = False
            self.parent = None
            return 

        self.parent = parent
        self.uuid = entry["ID"]
        self.version = entry["Version"]
        self.name = entry["VissibleName"]
        self.is_document = entry["Type"] == "DocumentType"
        self.success = entry["Success"]
        self.status = "-"

        try:
            self.modified_client = datetime.strptime(entry["ModifiedClient"], "%Y-%m-%dT%H:%M:%S.%fZ")
        except:
            self.modified_client = datetime.strptime(entry["ModifiedClient"], "%Y-%m-%dT%H:%M:%SZ")
        

    def modified_str(self):
        return self.modified_client.strftime("%Y-%m-%d %H:%M:%S")

class Collection(Item):

    def __init__(self, entry, parent):
        super(Collection, self).__init__(entry, parent)
        pass

    def add_child(self, child: Item):
        self.children.append(child)


class Document(Item):

    def __init__(self, entry, parent: Collection):
        super(Document, self).__init__(entry, parent)
        self.download_url = None
        self.path = "data/%s" % self.uuid
        self.update_status()

    def update_status(self):
        self.status = "Available" if os.path.exists(self.path) else "-"

#
# HELPER FUNCTIONS
#
def create_tree(entries):

    lookup_table = {}
    for i in range(len(entries)):
        lookup_table[entries[i]["ID"]] = i

    # Create a dummy root object where everything starts
    root = Collection(None, None)
    items = {
        "": root
    }

    for i in range(len(entries)):
        _create_tree_recursive(i, entries, items, lookup_table)

    return root


def _create_tree_recursive(i, entries, items, lookup_table):
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
            _create_tree_recursive(parent_id, entries, items, lookup_table)

    parent = items[parent_uuid]
    new_object = _item_factory(entry, parent)
    items[new_object.uuid] = new_object
        

def _item_factory(entry, parent):
    if entry["Type"] == "CollectionType":
        new_object = Collection(entry, parent)

    elif entry["Type"] == "DocumentType":
        new_object = Document(entry, parent)

    else: 
        raise Exception("Unknown type %s" % entry["Type"])
    
    parent.add_child(new_object)
    return new_object
