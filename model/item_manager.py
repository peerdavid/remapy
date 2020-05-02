import os
import shutil
import json 
from io import BytesIO
import zipfile
from zipfile import ZipFile

from api.remarkable_client import RemarkableClient
import model.item
from model.collection import Collection
from model.document import Document
from utils.helper import Singleton
import utils.config


class ItemManager(metaclass=Singleton):
    """ The ItemManager keeps track of all the collections and documents
        that are stored in your rm cloud. Load and create items through 
        this class. It is a singleton such that it is ensured that access to 
        items goes through the same tree structure.
    """
    

    def __init__(self,):
        self.rm_client = RemarkableClient()
        self.root = None


    def get_root(self, force=False):
        """ Get root node of tree from cache or download it from the rm cloud. 
            If you are offline, we load the stored tree from last time.
            Note that if we are online we sync all files with the rm cloud 
            i.e. delete old local files.
        """
        if not self.root is None and not force:
            return self.root

        metadata_list, is_online = self._get_metadata_list()
        
        self._clean_local_items(metadata_list)
        self.root = self._create_tree(metadata_list)
        return self.root, is_online


    def get_item(self, id, item=None):
        """ Get item object for given id. If item metadata is not already
            downloaded, it is downloaded beforehand.
        """
        self.get_root()
        
        item = self.root if item is None else item

        if item.id() == id:
            return item
        
        for child in item.children:
            found = self.get_item(id, child)
            if found != None:
                return found
        
        return None


    def create_backup(self, backup_path):
        # Create folder structure
        self.traverse_tree(
            fun=lambda item: item.create_backup(backup_path),
            document=False,
            collection=True)

        # And copy files into it
        self.traverse_tree(
            fun=lambda item: item.create_backup(backup_path),
            document=True,
            collection=False)
    

    def upload_file(self, id, parent_id, name, filetype, data, state_listener=None):
        metadata, mf = self._prepare_new_document_zip(
                id,
                name, 
                data,
                file_type=filetype, 
                parent_id = parent_id)

        # Upload file into cloud
        metadata = self.rm_client.upload(id, metadata, mf)

        # Download again to ensure that metadata is correct
        parent = self.get_item(parent_id)
        item = self._create_item(metadata, parent)

        if state_listener != None:
            item.add_state_listener(state_listener)

        # Download again to get it correctly
        item.sync()
        return item


    def traverse_tree(self, fun, item=None, document=True, collection=True):
        """ Traverse item tree (bottom up) and call fun for item depending on 
            whether document=True and colleciton=True.
        """
        item = self.get_root() if item == None else item
        
        for child in item.children:
            self.traverse_tree(fun, child, document, collection)
        
        if (item.is_document() and document) or (item.is_collection() and collection):
            fun(item)


    def _create_item(self, metadata, parent):
        if metadata["Type"] == "CollectionType":
            new_object = Collection(metadata, parent)

        elif metadata["Type"] == "DocumentType":
            new_object = Document(metadata, parent)

        else: 
            raise Exception("Unknown type %s" % metadata["Type"])
        
        parent.add_child(new_object)
        return new_object

        
    def _get_metadata_list(self):
        try:
            metadata_list = self.rm_client.list_items()
            return metadata_list, metadata_list != None
        except:
            metadata_list = []
            for local_id in os.listdir(utils.config.PATH):
                metadata_path = model.item.get_path_metadata_local(local_id)
                with open(metadata_path, 'r') as file:
                    metadata_content = file.read().replace('\n', '')
                
                metadata = json.loads(metadata_content)
                metadata_list.append(metadata)

        return metadata_list, False


    def _clean_local_items(self, metadata_list):
        online_ids = [metadata["ID"] for metadata in metadata_list]
        for local_id in os.listdir(utils.config.PATH):
            if local_id in online_ids:
                continue
            
            local_file_or_folder = "%s/%s" % (utils.config.PATH, local_id)
            if os.path.isfile(local_file_or_folder):
                os.remove(local_file_or_folder)
            else:
                shutil.rmtree(local_file_or_folder)
            print("Deleted local item %s" % local_id)


    def _create_tree(self, metadata_list):

        lookup_table = {}
        for i in range(len(metadata_list)):
            lookup_table[metadata_list[i]["ID"]] = i

        # Create a dummy root object where everything starts with parent 
        # "". This parent "" should not be changed as it is also used in 
        # the rm cloud
        root = Collection(None, None)
        items = {
            "": root
        }

        # We do this for every element, because _create_item_and_parents
        # only ensures that all parents already exist
        for i in range(len(metadata_list)):
            self._create_item_and_parents(i, metadata_list, items, lookup_table)

        return root


    def _create_item_and_parents(self, i, metadata_list, items, lookup_table):
        metadata = metadata_list[i]
        parent_id = metadata["Parent"]

        if i < 0 or len(metadata_list) <= 0 or metadata["ID"] in items:
            return

        if not parent_id in items:
            if not parent_id in lookup_table:
                print("(Warning) No parent for item %s" % metadata["VissibleName"])
                parent_id = ""
            else:
                parent_pos = lookup_table[parent_id]
                self._create_item_and_parents(parent_pos, metadata_list, items, lookup_table)

        parent = items[parent_id]
        new_object = self._create_item(metadata, parent)
        items[new_object.id()] = new_object


    def _prepare_new_document_zip(self, id, name, data, file_type, parent_id=""):

        # .content file
        content_file = json.dumps({
            "extraMetadata": { },
            "fileType": file_type,
            "pageCount": 0,
            "lastOpenedPage": 0,
            "lineHeight": -1,
            "margins": 180,
            "textScale": 1,
            "transform": { }
        })

        # metadata
        metadata = {
            "ID": id,
            "Parent": parent_id,
            "VissibleName": name,
            "Type": "DocumentType",
            "Version": 1,
            "ModifiedClient": model.item.now_rfc3339(),
            "CurrentPage": 0,
            "Bookmarked": False,
            # "Message": "",
            # "Success": True,
            # "BlobURLGet": "",
            # "BlobURLGetExpires": "",
            # "BlobURLPut": "",
            # "BlobURLPutExpires": ""
        }

        mf = BytesIO()
        mf.seek(0)
        with ZipFile(mf, mode='w', compression=zipfile.ZIP_DEFLATED ) as zf:
            zf.writestr("%s.%s" % (id, file_type), data)
            zf.writestr("%s.content" % id, content_file)
            zf.writestr("%s.pagedata" % id, "")

        # with open("test.zip", "wb") as f:
        #     f.write(mf.getvalue())
        mf.seek(0)
        return metadata, mf


