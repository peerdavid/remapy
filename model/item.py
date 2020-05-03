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


def now_rfc3339():
    return datetime.utcnow().strftime(RFC3339Nano)


#
# CLASS
#
class Item(object):

    #
    # CTOR
    #
    def __init__(self, metadata, parent=None):
        self.metadata = metadata
        self._parent = parent
        self._children = []
        self.path = get_path(self.id())
        self.path_remapy = get_path_remapy(self.id())
        self.path_metadata_local = get_path_metadata_local(self.id())

        self.rm_client = RemarkableClient()
        self.state_listener = []
        

    #
    # Getter and setter
    #
    def is_root(self):
        return self.metadata is None


    def id(self):
        return self._meta_value("ID")


    def name(self):
        return self._meta_value("VissibleName")


    def version(self):
        return self._meta_value("Version", -1)
    

    def bookmarked(self):
        return self._meta_value("Bookmarked", False)


    def is_document(self):
        return self._meta_value("Type", "CollectionType") == "DocumentType"
    

    def is_collection(self):
        return self._meta_value("Type", "CollectionType") != "DocumentType"
    

    def modified_time(self):
        modified = self.metadata["ModifiedClient"]
        try:
            utc = datetime.strptime(modified, "%Y-%m-%dT%H:%M:%S.%fZ")
        except:
            utc = datetime.strptime(modified, "%Y-%m-%dT%H:%M:%SZ")
        
        epoch = time.mktime(utc.timetuple())
        offset = datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)
        return utc + offset


    def parent(self):
        return self._parent
    
    def children(self):
        return self._children
    

    def _meta_value(self, key, root_value=""):
        if self.is_root():
            return root_value
        return self.metadata[key]


    #
    # Functions
    #
    def set_bookmarked(self, bookmarked):
        self.metadata["Bookmarked"] = bookmarked
        self.metadata["ModifiedClient"] = now_rfc3339()
        self.metadata["Version"] += 1
        self.rm_client.update_metadata(self.metadata)
        self._write_remapy_file()
        self._update_state_listener()


    def rename(self, new_name):
        self.metadata["VissibleName"] = new_name
        self.metadata["ModifiedClient"] = now_rfc3339()
        self.metadata["Version"] += 1
        self.rm_client.update_metadata(self.metadata)
        self._write_remapy_file()
        self._update_state_listener()


    def add_state_listener(self, listener):
        self.state_listener.append(listener)


    def _update_state_listener(self):
        for listener in self.state_listener:
            listener(self)
        

    def _write_remapy_file(self):
        if self.is_root():
            return 

        Path(self.path_remapy).mkdir(parents=True, exist_ok=True)
        with open(self.path_metadata_local, "w") as out:
            out.write(json.dumps(self.metadata, indent=4))