

import api.config as cfg


class Client(object):


    def __init__(self):
        self.test = True
        self.sign_in_subscribers = []

    #
    # EVENTS
    #

    def subscribe_sign_in(self, subscriber):
        """ Sends a signal (true) if successfully signed in 
            and (false) if login was not possible in rm cloud.
        """
        self.sign_in_subscribers.append(subscriber)

    #
    # API
    #

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

            # Inform all subscribers that we are successfully loged in        
            for subscriber in self.sign_in_subscribers:
                subscriber.sign_in_event_handler(False)

        else:
            # Inform all subscribers that we are successfully loged in        
            for subscriber in self.sign_in_subscribers:
                subscriber.sign_in_event_handler(True)
    



        