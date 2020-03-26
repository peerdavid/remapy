import os
import zipfile
from datetime import datetime

from api.client import Client
from api.helper import Singleton
import api.object.parser as parser
from api.object.item import Item
from api.object.collection import Collection

class Document(Item):

    def __init__(self, entry, parent: Collection):
        super(Document, self).__init__(entry, parent)
        
        self.path_raw = "data/%s" % self.uuid
        self.path_zip = "%s.zip" % self.path_raw
        self.path_svg = "%s/%s_" % (self.path_raw, self.name)
        self.path_rm_files = "%s/%s" % (self.path_raw, self.uuid)

        self.current_page = entry["CurrentPage"]
        self.current_svg_page = self.path_svg + str(self.current_page).zfill(5) + ".svg"
        self.status = "Available" if os.path.exists(self.path_raw) else "-"
        self.download_url = None
        self.blob_url = None


    def download_raw(self):
        
        if self.blob_url == None:
            self.blob_url = self.rm_client.get_blob_url(self.uuid)

        raw_file = self.rm_client.get_raw_file(self.blob_url)
        with open(self.path_zip, "wb") as out:
            out.write(raw_file)
        
        with zipfile.ZipFile(self.path_zip, "r") as zip_ref:
            zip_ref.extractall(self.path_raw)
        
        os.remove(self.path_zip)
        self.update_status = "Available"
    

    def download_svg(self):
        if self.status != "Available":
            self.download_raw()

        parser.rm_to_svg(self.path_rm_files, self.path_svg, background="white")
