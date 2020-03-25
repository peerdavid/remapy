

import api.config as cfg

# 
# EVENTS
#
EVENT_SUCCESS = 0
EVENT_FAILED = 1

# Auth events
EVENT_OFFLINE = 2
EVENT_ONETIMECODE_NEEDED = 3


#
# CONSTANTS
#
USER_AGENT = "remapy"
BASE_URL = "https://document-storage-production-dot-remarkable-production.appspot.com"
DEVICE_TOKEN_URL = "https://my.remarkable.com/token/json/2/device/new"
USER_TOKEN_URL = "https://my.remarkable.com/token/json/2/user/new"
DEVICE = "desktop-windows"
SERVICE_MGR_URL = "https://service-manager-production-dot-remarkable-production.appspot.com"


#
# CLIENT
#
class Client(object):
    def __init__(self):
        self.test = True
        self.sign_in_listener = []

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
        config = cfg.load()

        # Get device and usertoken from rm cloud
        if not cfg.exists("remarkable.authentication.user_token"):
            if onetime_code is None or onetime_code == "":
                self.publish(self.sign_in_listener, EVENT_ONETIMECODE_NEEDED)
                return

            device_token = self._get_device_token(onetime_code)
            if device_token is None:
                self.publish(self.sign_in_listener, EVENT_FAILED)
                return
            
            user_token = self._get_user_token(device_token)
            if user_token is None:
                self.publish(self.sign_in_listener, EVENT_FAILED)
                return

            config = cfg.save({"remarkable": {
                "authentication": {
                    "onetime_code": onetime_code,
                    "device_token": device_token,
                    "user_token": user_token
                }
            }})


        # Inform all subscribers that we are successfully loged in        
        auth = config["remarkable"]["authentication"]
        self.publish(self.sign_in_listener, EVENT_SUCCESS, auth)
        return auth
    

    def _get_device_token(self, one_time_code):
        if one_time_code is None:
            return None
        return "salkdjf-sldif-342"


    def _get_user_token(self, device_token):
        if device_token is None:
            return None
        return "dev-kdsjf9-298347"




        