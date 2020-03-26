from datetime import datetime
from api.client import Client



class Item(object):

    STATE_UNKNOWN = 0
    STATE_COLLECTION = 1
    STATE_DOCUMENT_ONLINE = 2
    STATE_DOCUMENT_LOCAL_NOTEBOOK = 3
    STATE_DOCUMENT_LOCAL_PDF = 4
    STATE_DOCUMENT_LOCAL_EBUB = 5
    STATE_DOCUMENT_OUT_OF_SYNC = 6
    STATE_DOCUMENT_DOWNLOADING = 7

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
        self.current_page = "-"

        try:
            self.modified_client = datetime.strptime(entry["ModifiedClient"], "%Y-%m-%dT%H:%M:%S.%fZ")
        except:
            self.modified_client = datetime.strptime(entry["ModifiedClient"], "%Y-%m-%dT%H:%M:%SZ")
        

    def modified_str(self):
        return self.modified_client.strftime("%Y-%m-%d %H:%M:%S")
