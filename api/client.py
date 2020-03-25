
import os
import zipfile
from io import BytesIO
import requests
from uuid import uuid4
from pathlib import Path

import api.config as cfg
from api.objects import Collection, Document, create_tree

# 
# EVENTS
#
EVENT_SUCCESS = 0
EVENT_FAILED = 1

# Auth events
EVENT_DEVICE_TOKEN_FAILED = 2
EVENT_USER_TOKEN_FAILED = 3
EVENT_ONETIMECODE_NEEDED = 4


#
# CONSTANTS
#
USER_AGENT = "remapy"
BASE_URL = "https://document-storage-production-dot-remarkable-production.appspot.com"
DEVICE_TOKEN_URL = "https://my.remarkable.com/token/json/2/device/new"
USER_TOKEN_URL = "https://my.remarkable.com/token/json/2/user/new"
DEVICE = "desktop-windows"
SERVICE_MGR_URL = "https://service-manager-production-dot-remarkable-production.appspot.com"

LIST_DOCS_URL = BASE_URL + "/document-storage/json/2/docs"
UPDATE_STATUS_URL = BASE_URL + "/document-storage/json/2/upload/update-status"
UPLOAD_REQUEST_URL = BASE_URL + "/document-storage/json/2/upload/request"
DELETE_ENTRY_URL = BASE_URL + "/document-storage/json/2/delete"


#
# CLIENT
#
class Client(object):
    def __init__(self):
        self.test = True
        self.sign_in_listener = []
        self.root = None

    #
    # EVENT HANDLER
    #
    def listen_sign_in(self, subscriber):
        """ Sends a signal (true) if successfully signed in 
            and (false) if login was not possible in rm cloud.
        """
        self.sign_in_listener.append(subscriber)
    
    def publish(self, subscribers, code=EVENT_SUCCESS, data=None):
        for subscriber in subscribers:
            subscriber.sign_in_event_handler(code, data)

    #
    # API
    #
    def sign_in(self, onetime_code=None):
        """ Load token. If not available the user must provide a 
            one time code from https://my.remarkable.com/connect/remarkable
        """ 
        # Get device token if not stored local
        device_token = cfg.get("remarkable.authentication.device_token")
        if device_token == None:
            if onetime_code is None or onetime_code == "":
                self.publish(self.sign_in_listener, EVENT_ONETIMECODE_NEEDED)
                return

            device_token = self._get_device_token(onetime_code)
            if device_token is None:
                self.publish(self.sign_in_listener, EVENT_DEVICE_TOKEN_FAILED)
                return            
        
        # Renew the user token.
        user_token = self._get_user_token(device_token)
        if user_token is None:
            self.publish(self.sign_in_listener, EVENT_USER_TOKEN_FAILED)
            return
        
        # Save tokens to config
        auth = {"device_token": device_token,
                "user_token": user_token}
        cfg.save({"remarkable": {"authentication": auth}})

        # Inform all subscriber
        self.publish(self.sign_in_listener, EVENT_SUCCESS, auth)
        return auth
    

    def get_root(self):
        response = self._request("GET", LIST_DOCS_URL)

        if response.ok:
            items = response.json()
            self.root = create_tree(items)
            return self.root
        
        return None
    

    def get_item(self, uuid):
        if self.root is None:
            self.get_root()

        return self._get_item_rec(self.root, uuid)
    

    def _get_blob_url(self, uuid):
        
        response = self._request("GET", LIST_DOCS_URL, params={
            "doc": uuid,
            "withBlob": True
        })
        
        if response.ok:
            items = response.json()
            return items[0]["BlobURLGet"]
        
        return None
    

    def download_file(self, uuid):
        item = self.get_item(uuid)
        blob_url = self._get_blob_url(uuid)

        stream = self._request("GET", blob_url, stream=True)
        zip_io = BytesIO()
        for chunk in stream.iter_content(chunk_size=8192):
            zip_io.write(chunk)
        
        path = "data" # ToDo: Create user settings
        Path(path).mkdir(parents=True, exist_ok=True)
        file_name = "%s/%s.zip" % (path, item.uuid)
        with open(file_name, "wb") as out:
            out.write(zip_io.getbuffer())
        
        with zipfile.ZipFile(file_name, "r") as zip_ref:
            zip_ref.extractall("%s/%s" % (path, item.uuid))
        
        os.remove(file_name)
        item.update_status()
        return item


    def _get_item_rec(self, root, uuid):
        if root.uuid == uuid:
            return root
        
        for child in root.children:
            found = self._get_item_rec(child, uuid)
            if found != None:
                return found

        return None


    def _get_device_token(self, one_time_code):
        """ Create a new device for a given one_time_code to be able to 
            connect to the rm cloud
        """ 
        body = {
            "code": one_time_code,
            "deviceDesc": DEVICE,
            "deviceID": str(uuid4()),
        }
        response = self._request("POST", DEVICE_TOKEN_URL, body=body)
        if response.ok:
            device_token = response.text
            return device_token
        return None


    def _get_user_token(self, device_token):
        """ This is the second step of the authentication of the Remarkable Cloud.
            Before each new session, you should fetch a new user token.
            User tokens have an unknown expiration date.
        """
        if device_token is None or device_token == "":
            return None
        
        response = self._request("POST", USER_TOKEN_URL, None, headers={
                "Authorization": f"Bearer {device_token}"
        })

        if response.ok:
            user_token = response.text
            return user_token
        return None
    

    def _request(self, method, path,
                data=None, body=None, headers=None,
                params=None, stream=False):
        """Creates a request against the Remarkable Cloud API
        This function automatically fills in the blanks of base
        url & authentication.
        Credit: https://github.com/subutux/rmapy/blob/master/rmapy/api.py
        Args:
            method: The request method.
            path: complete url or path to request.
            data: raw data to put/post/...
            body: the body to request with. This will be converted to json.
            headers: a dict of additional headers to add to the request.
            params: Query params to append to the request.
            stream: Should the response be a stream?
        Returns:
            A Response instance containing most likely the response from
            the server.
        """

        config = cfg.load()

        if headers is None:
            headers = {}
       
        if not path.startswith("http"):
            if not path.startswith('/'):
                path = '/' + path
            url = f"{BASE_URL}{path}"
        else:
            url = path

        _headers = {
            "user-agent": USER_AGENT,
        }

        user_token = cfg.get("remarkable.authentication.user_token")
        if user_token != None:
            _headers["Authorization"] = f"Bearer {user_token}"
        
        for k in headers.keys():
            _headers[k] = headers[k]
        
        r = requests.request(method, url,
                             json=body,
                             data=data,
                             headers=_headers,
                             params=params,
                             stream=stream)
        return r



        