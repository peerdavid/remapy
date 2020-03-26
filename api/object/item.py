from datetime import datetime
from api.client import Client



class Item(object):

    STATE_UNKNOWN = 0
    STATE_ONLINE = 1
    STATE_SYNCED = 2
    STATE_SYNCED_OUT_OF_SYNC = 3

    def __init__(self, entry, parent=None):
        self.children = []
        is_root = entry is None
        if is_root:
            self.uuid = ""
            self.is_document = False
            self.parent = None
            return 

        self.rm_client = Client()
        self.parent = parent
        self.uuid = entry["ID"]
        self.version = entry["Version"]
        self.name = entry["VissibleName"]
        self.is_document = entry["Type"] == "DocumentType"
        self.success = entry["Success"]
        self.state = self.STATE_UNKNOWN

        try:
            self.modified_client = datetime.strptime(entry["ModifiedClient"], "%Y-%m-%dT%H:%M:%S.%fZ")
        except:
            self.modified_client = datetime.strptime(entry["ModifiedClient"], "%Y-%m-%dT%H:%M:%SZ")
        

    def modified_str(self):
        return self.modified_client.strftime("%Y-%m-%d %H:%M:%S")
