from datetime import datetime
import time
from pathlib import Path
import json

from api.remarkable_client import RemarkableClient
import utils.config


#
# DEFINITIONS
#
STATE_SYNCING = 1
STATE_SYNCED = 2
STATE_DELETED = 170591

RFC3339Nano = "%Y-%m-%dT%H:%M:%SZ"


#
# HELPER
#
def get_path(id):
    return "%s/%s" % (utils.config.PATH, id)

def get_path_remapy(id):    
    return "%s/.remapy" % get_path(id)

def get_path_metadata_local(id):
    return "%s/metadata.local" % get_path_remapy(id)


#
# CLASS
#
class Item(object):

    def __init__(self, metadata, parent=None):
        self.children = []
        self.is_root = metadata is None
        if self.is_root:
            self.id = ""
            self.is_document = False
            self.parent = None
            self.is_collection = True
            self.is_document = False
            return 

        self.metadata = metadata
        self.rm_client = RemarkableClient()
        self.parent = parent
        self.id = metadata["ID"]
        self.version = metadata["Version"]
        self.name = metadata["VissibleName"]
        self.is_document = metadata["Type"] == "DocumentType"
        self.is_collection = not self.is_document
        self.success = metadata["Success"]
        self.bookmarked = metadata["Bookmarked"]
        self.current_page = "-"
        self.state_listener = []

        try:
            self.modified_client = datetime.strptime(metadata["ModifiedClient"], "%Y-%m-%dT%H:%M:%S.%fZ")
        except:
            self.modified_client = datetime.strptime(metadata["ModifiedClient"], "%Y-%m-%dT%H:%M:%SZ")
        
        # Set paths
        self.path = get_path(self.id)
        self.path_remapy = get_path_remapy(self.id)
        self.path_metadata_local = get_path_metadata_local(self.id)
        

    def get_metadata(self):
        return self.metadata
    
    def set_bookmarked(self, bookmarked):
        self.bookmarked = bookmarked
        self.metadata["Bookmarked"] = bookmarked
        self.metadata["ModifiedClient"] = datetime.datetime.utcnow().strftime(RFC3339Nano)
        self.metadata["Version"] += 1

    def is_root_item(self):
        return self.parent is None or self.parent == ""

    def local_modified_time(self):
        local_time = self._from_utc_to_local_time(self.modified_client)
        return local_time.strftime("%Y-%m-%d %H:%M:%S")

    def add_state_listener(self, listener):
        self.state_listener.append(listener)

    def _update_state_listener(self):
        for listener in self.state_listener:
            listener(self)


    def _from_utc_to_local_time(self, utc):
        epoch = time.mktime(utc.timetuple())
        offset = datetime.fromtimestamp (epoch) - datetime.utcfromtimestamp (epoch)
        return utc + offset
        
    def _write_remapy_metadata(self):
        if self.is_root:
            return 

        Path(self.path_remapy).mkdir(parents=True, exist_ok=True)
        with open(self.path_metadata_local, "w") as out:
            out.write(json.dumps(self.metadata, indent=4))