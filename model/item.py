from datetime import datetime
import time
from pathlib import Path
import json

from api.remarkable_client import RemarkableClient
import utils.config


STATE_SYNCING = 1
STATE_SYNCED = 2
STATE_DELETED = 170591


class Item(object):

    def __init__(self, entry, parent=None):
        self.children = []
        self.is_root = entry is None
        if self.is_root:
            self.id = ""
            self.is_document = False
            self.parent = None
            self.is_collection = True
            self.is_document = False
            return 

        self.entry = entry
        self.rm_client = RemarkableClient()
        self.parent = parent
        self.id = entry["ID"]
        self.version = entry["Version"]
        self.name = entry["VissibleName"]
        self.is_document = entry["Type"] == "DocumentType"
        self.is_collection = not self.is_document
        self.success = entry["Success"]
        self.current_page = "-"
        self.state_listener = []

        try:
            self.modified_client = datetime.strptime(entry["ModifiedClient"], "%Y-%m-%dT%H:%M:%S.%fZ")
        except:
            self.modified_client = datetime.strptime(entry["ModifiedClient"], "%Y-%m-%dT%H:%M:%SZ")
        
        # Set paths
        self.path = "%s/%s" % (utils.config.PATH, self.id)
        self.path_remapy = "%s/.remapy" % self.path
        self.path_metadata_local = "%s/metadata.local" % self.path_remapy
        
        
    def is_root_item(self):
        return self.parent is None or self.parent == ""


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

        
    def _write_remapy_metadata(self):
        if self.is_root:
            return 
            
        Path(self.path_remapy).mkdir(parents=True, exist_ok=True)
        with open(self.path_metadata_local, "w") as out:
            out.write(json.dumps(self.entry, indent=4))