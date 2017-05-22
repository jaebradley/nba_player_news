import json
import logging
import logging.config

import requests

from environment import FACEBOOK_PAGE_ACCESS_TOKEN


class FacebookMessager:
    logger = logging.getLogger("facebookMessager")

    def __init__(self):
        self.base_url = "https://graph.facebook.com/v2.6/me/messages"
        self.base_parameters = {"access_token": FACEBOOK_PAGE_ACCESS_TOKEN}
        self.headers = {"Content-Type": "application/json"}

    def send(self, recipient_id, message):
        FacebookMessager.logger.info("Sending message: {} to {}".format(message, recipient_id))

        r = requests.post(url=self.base_url, params=self.base_parameters, headers=self.headers,
                          data=FacebookMessager.build_data(recipient_id=recipient_id, message=message))

        FacebookMessager.logger.info("Status Code: {} | Response: {}".format(r.status_code, r.json()))

        return r

    @staticmethod
    def build_data(recipient_id, message):
        return json.dumps({
            "recipient": {
                "id": recipient_id
            },
            "message": {
                "text": message
            }
        })






