
import os
from io import BytesIO
import requests
from uuid import uuid4
from pathlib import Path
import json

import utils.config as cfg
from utils.helper import Singleton

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
DEVICE_TOKEN_URL = "https://webapp-production-dot-remarkable-production.appspot.com/token/json/2/device/new"
USER_TOKEN_URL = "https://webapp-production-dot-remarkable-production.appspot.com/token/json/2/user/new"
DEVICE = "mobile-android"
SERVICE_MGR_URL = "https://service-manager-production-dot-remarkable-production.appspot.com"

LIST_DOCS_URL = BASE_URL + "/document-storage/json/2/docs"
UPDATE_STATUS_URL = BASE_URL + "/document-storage/json/2/upload/update-status"
UPLOAD_REQUEST_URL = BASE_URL + "/document-storage/json/2/upload/request"
DELETE_ENTRY_URL = BASE_URL + "/document-storage/json/2/delete"


#
# CLIENT
#
class RemarkableClient():
    """ Client to connect to rm cloud via REST
    """

    class SignInListenerHandler(metaclass=Singleton):

        def __init__(self):
            self.sign_in_listener = []

        def listen_sign_in_event(self, subscriber):
            """ Sends a signal (true) if successfully signed in
                and (false) if login was not possible in rm cloud.
            """
            self.sign_in_listener.append(subscriber)

        def publish(self, code=EVENT_SUCCESS, data=None):
            for subscriber in self.sign_in_listener:
                try:
                    subscriber.sign_in_event_handler(code, data)
                except Exception as e:
                    print("(Warning) Failed to publish subscriber.")
                    print(e)


    def __init__(self):
        self.test = True
        self.listener_handler = self.SignInListenerHandler()

    def listen_sign_in_event(self, subscriber):
        self.listener_handler.listen_sign_in_event(subscriber)


    def sign_in(self, onetime_code=None):
        """ Load token. If not available the user must provide a
            one time code from https://my.remarkable.com/connect/remarkable
        """

        try:
            # Get device token if not stored local
            device_token = cfg.get("authentication.device_token")
            if device_token == None:
                if onetime_code is None or onetime_code == "":
                    self.listener_handler.publish(EVENT_ONETIMECODE_NEEDED)
                    return

                device_token = self._get_device_token(onetime_code)
                if device_token is None:
                    self.listener_handler.publish(EVENT_DEVICE_TOKEN_FAILED)
                    return

            # Renew the user token.
            user_token = self._get_user_token(device_token)
            if user_token is None:
                self.listener_handler.publish(EVENT_USER_TOKEN_FAILED)
                return

            # Save tokens to config
            auth = {"device_token": device_token,
                    "user_token": user_token}
            cfg.save({"authentication": auth})

            # Inform all subscriber
            self.listener_handler.publish(EVENT_SUCCESS, auth)
        except:
            auth={}
            self.listener_handler.publish(EVENT_FAILED, auth)

        return auth


    def get_item(self, id):

        response = self._request("GET", LIST_DOCS_URL, params={
            "doc": id,
            "withBlob": True
        })

        if response.ok:
            items = response.json()
            return items[0]

        return None


    def delete_item(self, id, version):

        response = self._request("PUT", DELETE_ENTRY_URL, body=[{
            "ID": id,
            "Version": version
        }])

        if response.ok:
            return True

        return False


    def list_items(self):
        response = self._request("GET", LIST_DOCS_URL)

        if response.ok:
            items = response.json()

            # Logging only
            # items_str = json.dumps(items, indent=4)
            # with open("all_files.json", "wt") as f:
            #     f.write(items_str)

            return items
        return None


    def get_raw_file(self, blob_url):
        stream = self._request("GET", blob_url, stream=True)
        zip_io = BytesIO()
        for chunk in stream.iter_content(chunk_size=8192):
            zip_io.write(chunk)
        return zip_io.getbuffer()


    def upload(self, id, metadata, zip_file):
        response = self._request("PUT", "/document-storage/json/2/upload/request",
                           body=[{
                               "ID": id,
                               "Type": "DocumentType",
                               "Version": 1
                           }])
        if not response.ok:
            print("(Error) Upload request failed")
            return

        response = response.json()
        blob_url = response[0].get("BlobURLPut", None)

        response = self._request("PUT", blob_url, data=zip_file.getvalue())
        zip_file.seek(0)
        if not response.ok:
            print("(Error) Upload request failed")
            return

        return self.update_metadata(metadata)


    def update_metadata(self, metadata):
        response = self._request("PUT", UPDATE_STATUS_URL, body=[metadata])
        if not response.ok:
            print("(Error) Upload request failed")
            return

        return self.get_item(metadata["ID"])


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

        try:
            response = self._request("POST", USER_TOKEN_URL, None, headers={
                    "Authorization": "Bearer %s" % device_token
            })
        except:
            return None

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
            url = "%s%s" % (BASE_URL, path)
        else:
            url = path

        _headers = {
            "user-agent": USER_AGENT,
        }

        user_token = cfg.get("authentication.user_token")
        if user_token != None:
            _headers["Authorization"] = "Bearer %s" % user_token

        for k in headers.keys():
            _headers[k] = headers[k]

        r = requests.request(method, url,
                             json=body,
                             data=data,
                             headers=_headers,
                             params=params,
                             stream=stream,
                             timeout=60*2)
        return r



