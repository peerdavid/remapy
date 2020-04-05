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
import model.render as render
import model.item
from model.item import Item
from model.collection import Collection
import utils.config as cfg


# Document type states
TYPE_UNKNOWN = 0       # If it is only online we don't know the state
TYPE_NOTEBOOK = 1
TYPE_PDF = 2
TYPE_EPUB = 3

# Synced with cloud states
STATE_NOT_SYNCED = 200
STATE_OUT_OF_SYNC = 201


class Document(Item):


    def __init__(self, entry, parent: Collection):
        super(Document, self).__init__(entry, parent)
        
        # Remarkable tablet paths
        self.path_zip = "%s.zip" % self.path
        self.path_rm_files = "%s/%s" % (self.path, self.id)

        # RemaPy paths
        self.path_annotated_pdf = "%s/%s.pdf" % (self.path_remapy, self.name)
        self.path_original_pdf = "%s/%s.pdf" % (self.path, self.id)
        self.path_original_epub = "%s/%s.epub" % (self.path, self.id)

        # Other props
        self.current_page = entry["CurrentPage"] + 1
        self.download_url = None
        self.blob_url = None
        self.state = None       # Synced, out of sync etc.
        self.type = None        # Unknown (not downloaded yet), pdf, epub or notebook

        # Set correct state of document
        self._update_state()


    def delete_local(self):
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
        self._update_state()
    

    def delete(self):
        ok = self.rm_client.delete_item(self.id, self.version)

        if ok:
            self.state = model.item.STATE_DELETED
            self._update_state_listener()
        return ok


    def is_parent_of(self, item):
        return False

    def full_name(self):
        return "%s/%s" % (self.parent.full_name(), self.name)

    def sync(self):
        if self.state == model.item.STATE_SYNCING:
            return 
            
        self.state = model.item.STATE_SYNCING
        self._update_state_listener()

        self._download_raw()
        self._write_remapy_metadata()
        self._update_state(inform_listener=False)

        annotations_exist = os.path.exists(self.path_rm_files)

        if self.type == TYPE_NOTEBOOK and annotations_exist:
            render.notebook(
                self.path, 
                self.id, 
                self.path_annotated_pdf,
                path_templates=cfg.get("general.templates"))
        
        else:
            if annotations_exist:
                # Also for epubs a pdf file exists which we can annotate :)
                # We will then show the pdf rather than the epub...
                render.pdf(
                    self.path_rm_files, 
                    self.path_original_pdf,
                    self.path_annotated_pdf)

        self._update_state()
        self.parent.sync()


    def get_annotated_or_original_file(self):
        if os.path.exists(self.path_annotated_pdf):
            return self.path_annotated_pdf
        
        return self.get_original_file()
    

    def get_original_file(self):
        if self.type == TYPE_EPUB:
            return self.path_original_epub
        if self.type == TYPE_NOTEBOOK:
            return self.path_annotated_pdf
        else:
            return self.path_original_pdf


    def _download_raw(self, path=None):
        path = self.path if path == None else path

        if os.path.exists(path):
            shutil.rmtree(path)

        if self.blob_url == None:
            self.blob_url = self.rm_client.get_item(self.id)["BlobURLGet"]

        raw_file = self.rm_client.get_raw_file(self.blob_url)
        with open(self.path_zip, "wb") as out:
            out.write(raw_file)
        
        with zipfile.ZipFile(self.path_zip, "r") as zip_ref:
            zip_ref.extractall(path)
        
        os.remove(self.path_zip)

        # Update state
        self._update_state(inform_listener=False)
    

    def update_state(self):
        self._update_state(inform_listener=True)


    def _update_state(self, inform_listener=True):
        
        # Not synced
        if not os.path.exists(self.path_metadata_local):
            self.type = TYPE_UNKNOWN
            self.state = STATE_NOT_SYNCED
        
        # If synced get file type
        else:
            with open(self.path_metadata_local, encoding='utf-8') as f:
                local_metadata = json.loads(f.read())

            self.state = model.item.STATE_SYNCED if local_metadata["Version"] == self.version else STATE_OUT_OF_SYNC
            is_epub = os.path.exists(self.path_original_epub)
            is_pdf = not is_epub and os.path.exists(self.path_original_pdf)

            if is_epub:
                self.type = TYPE_EPUB
            elif is_pdf:
                self.type = TYPE_PDF
            else:
                self.type = TYPE_NOTEBOOK

        # Inform listener if needed
        if not inform_listener:
            return 

        self._update_state_listener()


    def create_backup(self, backup_path):
        
        backup_path = "%s/%s" % (backup_path, self.parent.full_name())
        Path(backup_path).mkdir(parents=True, exist_ok=True)

        file_to_backup = self.get_annotated_or_original_file()
        extension = os.path.splitext(file_to_backup)[1]
        file_name = self.name + extension
        shutil.copyfile(file_to_backup, backup_path + "/" + file_name)

        
def create_document_zip(file_path, file_type, parent_id=""):
    id = str(uuid.uuid4())

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
        "Type": "DocumentType",
        "Version": 1,
        "ID": id,
        "Parent": parent_id,
        "ModifiedClient": timestamp,
        #"Success": True,
        "CurrentPage": 0,
        "Bookmarked": False,
    }

    mf = BytesIO()
    mf.seek(0)
    with ZipFile(mf, mode='w', compression=zipfile.ZIP_DEFLATED ) as zf:
        zf.write(file_path, arcname="%s.%s" % (id, file_type))
        zf.writestr("%s.content" % id, content_file)
        zf.writestr("%s.pagedata" % id, "")

    # with open("test.zip", "wb") as f:
    #     f.write(mf.getvalue())
    mf.seek(0)
    return id, metadata, mf


