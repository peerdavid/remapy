

import api.config as cfg


class Client(object):


    def __init__(self):
        self.test = True

    def sign_in(self):
        """ Load token. If not available the user must provide a 
            one time code from https://my.remarkable.com/connect/remarkable
        """ 
        config = cfg.load()

        if not cfg.exists("remarkable.device_token"):
            auth = {
                "device_token": "TEST",
                "user_token": "TEST"
            }
            cfg.save({"remarkable": auth})
            print("https://my.remarkable.com/connect/remarkable")
        
        print("SIGNED IN")
        