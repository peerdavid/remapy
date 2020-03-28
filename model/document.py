import os
from io import BytesIO
import zipfile
import uuid
from zipfile import ZipFile
import shutil
from pathlib import Path
from datetime import datetime, timezone
import json


from api.remarkable_client import RemarkableClient
from utils.helper import Singleton
import model.parser as parser
from model.item import Item
from model.collection import Collection
import utils.config as cfg

class Document(Item):
    
    PATH = Path.joinpath(Path.home(), ".remapy/cache")

    def __init__(self, entry, parent: Collection):
        super(Document, self).__init__(entry, parent)
        
        # Remarkable tablet paths
        self.path = "%s/%s" % (self.PATH, self.uuid)
        self.path_zip = "%s.zip" % self.path
        self.path_rm_files = "%s/%s" % (self.path, self.uuid)

        # RemaPy paths
        self.path_remapy = "%s/.remapy" % self.path
        self.path_original_pdf = "%s/%s.pdf" % (self.path, self.uuid)
        self.path_annotated_pdf = "%s/%s.pdf" % (self.path, self.name)

        # Other props
        self.current_page = entry["CurrentPage"]
        self.download_url = None
        self.blob_url = None

        # Set correct state of document
        self._update_state()


    def clear_cache(self):
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
        self._update_state()
    

    def delete(self):
        ok = self.rm_client.delete_item(self.uuid, self.version)

        if ok:
            self._update_state(state=self.STATE_DELETED)
        return ok


    def is_parent_of(self, item):
        return False


    def sync(self, force=False):

        must_sync = (self.state == self.STATE_DOCUMENT_ONLINE) or \
                    (self.state == self.STATE_DOCUMENT_OUT_OF_SYNC)
        
        if not force and not must_sync:
            return 
        
        self._download_raw()
        self._write_remapy_metadata()

        annotations_exist = os.path.exists(self.path_rm_files)

        if self.state == self.STATE_DOCUMENT_LOCAL_NOTEBOOK and annotations_exist:
            parser.parse_notebook(
                self.path, 
                self.uuid, 
                self.path_annotated_pdf,
                path_templates=cfg.get("general.templates"))
        
        elif self.state == self.STATE_DOCUMENT_LOCAL_PDF:
            if annotations_exist:
                parser.parse_pdf(self.path_rm_files, self.path_original_pdf, self.path_annotated_pdf)
            else:
                shutil.copyfile(self.path_original_pdf, self.path_annotated_pdf)
        
        self._update_state()


    def _download_raw(self, path=None):
        self._update_state(state=Item.STATE_DOCUMENT_DOWNLOADING)
        path = self.path if path == None else path

        if os.path.exists(path):
            shutil.rmtree(path)

        if self.blob_url == None:
            self.blob_url = self.rm_client.get_item(self.uuid)["BlobURLGet"]

        raw_file = self.rm_client.get_raw_file(self.blob_url)
        with open(self.path_zip, "wb") as out:
            out.write(raw_file)
        
        with zipfile.ZipFile(self.path_zip, "r") as zip_ref:
            zip_ref.extractall(path)
        
        os.remove(self.path_zip)

        # Update state
        self._update_state(inform_listener=False)
    

    def update_state(self):
        self._update_state(inform_listener=True, state=None)


    def _update_state(self, inform_listener=True, state=None):

        if state is None:
            if not os.path.exists(self.path):
                self.state = Item.STATE_DOCUMENT_ONLINE
            
            elif os.path.exists(self.path_original_pdf):
                self.state = Item.STATE_DOCUMENT_LOCAL_PDF

            else:
                self.state = Item.STATE_DOCUMENT_LOCAL_NOTEBOOK
        else:
            self.state = state
        
        if not inform_listener:
            return 

        self._update_state_listener()


    def _write_remapy_metadata(self):
        Path(self.path_remapy).mkdir(parents=True, exist_ok=True)
        with open("%s/metadata.yaml" % self.path_remapy, "w") as out:
            out.write(self.local_modified_time())

        
def create_document_zip( file_path, file_type="pdf", parent_id=""):
    ID = str(uuid.uuid4())

    # .content file
    content_file = json.dumps({
        "extraMetadata": { },
        "lastOpenedPage": 0,
        "lineHeight": -1,
        "margins": 180,
        "pageCount": 0,
        "textScale": 1,
        "transform": {},
        "fileType": file_type
    })

    # metadata
    timestamp = datetime.now(timezone.utc).astimezone().isoformat()
    metadata = {
        "VissibleName": os.path.splitext(os.path.basename(file_path))[0],
        #"deleted": False,
        #"lastModified": "1568368808000",
        #"metadatamodified": True,
        #"modified": True,
        #"parent": "",
        #"pinned": False,
        #"synced": True,
        "Type": "DocumentType",
        "Version": 1,
        "ID": ID,
        "Parent": parent_id,
        "ModifiedClient": timestamp
    }

    mf = BytesIO()
    mf.seek(0)
    with ZipFile(mf, mode='w', compression=zipfile.ZIP_DEFLATED ) as zf:
        zf.write(file_path, arcname="%s.%s" % (ID, file_type))
        zf.writestr("%s.content" % ID, content_file)
        zf.writestr("%s.pagedata" % ID, "")

    # with open("test.zip", "wb") as f:
    #     f.write(mf.getvalue())
    mf.seek(0)
    return ID, metadata, mf

