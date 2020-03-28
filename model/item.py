from datetime import datetime
from api.remarkable_client import RemarkableClient
import time

class Item(object):

    STATE_UNKNOWN = 0
    STATE_COLLECTION = 1
    STATE_DOCUMENT_ONLINE = 2
    STATE_DOCUMENT_LOCAL_NOTEBOOK = 3
    STATE_DOCUMENT_LOCAL_PDF = 4
    STATE_DOCUMENT_LOCAL_EBUB = 5
    STATE_DOCUMENT_OUT_OF_SYNC = 6
    STATE_DOCUMENT_DOWNLOADING = 7
    STATE_DELETED = 99

    def __init__(self, entry, parent=None):
        self.children = []
        is_root = entry is None
        if is_root:
            self.id = ""
            self.is_document = False
            self.parent = None
            return 

        self.rm_client = RemarkableClient()
        self.parent = parent
        self.id = entry["ID"]
        self.version = entry["Version"]
        self.name = entry["VissibleName"]
        self.is_document = entry["Type"] == "DocumentType"
        self.success = entry["Success"]
        self.state = self.STATE_UNKNOWN
        self.current_page = "-"
        self.state_listener = []

        try:
            self.modified_client = datetime.strptime(entry["ModifiedClient"], "%Y-%m-%dT%H:%M:%S.%fZ")
        except:
            self.modified_client = datetime.strptime(entry["ModifiedClient"], "%Y-%m-%dT%H:%M:%SZ")
        

    def local_modified_time(self):
        local_time = self._from_utc_to_local_time(self.modified_client)
        return local_time.strftime("%Y-%m-%d %H:%M:%S")


    def _from_utc_to_local_time(self, utc):
        epoch = time.mktime(utc.timetuple())
        offset = datetime.fromtimestamp (epoch) - datetime.utcfromtimestamp (epoch)
        return utc + offset


    def add_state_listener(self, listener):
        self.state_listener.append(listener)
    

    def _update_state_listener(self):
        for listener in self.state_listener:
            listener(self)