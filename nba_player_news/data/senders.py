import json
import logging
import logging.config

import requests
import tweepy
import yagmail

from environment import GMAIL_PASSWORD, GMAIL_USERNAME, TWITTER_ACCESS_SECRET, TWITTER_ACCESS_TOKEN, \
    TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, FACEBOOK_PAGE_ACCESS_TOKEN
from nba_player_news.data.sent_message_builders import EmailMessageBuilder, TwitterMessageBuilder


class Emailer:
    logger = logging.getLogger("emailer")

    def __init__(self):
        self.client = yagmail.SMTP(user=GMAIL_USERNAME, password=GMAIL_PASSWORD)

    def send(self, destination, message):
        Emailer.logger.info("Sending message on behalf of user: {} to {} with message: {}".format(GMAIL_USERNAME, destination, message))
        self.client.send(
            to=destination,
            subject=message["headline"],
            contents=EmailMessageBuilder(message=message).build()
        )


class Tweeter:
    logger = logging.getLogger("tweeter")

    def __init__(self):
        auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
        auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
        self.client = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)

    def send(self, user_id, message):
        self.client.send_direct_message(user_id=user_id, text=TwitterMessageBuilder(message=message).build())


class FacebookMessager:
    logger = logging.getLogger("facebookMessager")

    def __init__(self):
        self.base_url = "https://graph.facebook.com/v2.6/me/messages"
        self.base_parameters = {
            "access_token": FACEBOOK_PAGE_ACCESS_TOKEN
        }
        self.headers = {
            "Content-Type": "application/json"
        }

    def send(self, recipient_id, message):
        FacebookMessager.logger.info("Sending message: {} to {}".format(message, recipient_id))

        r = requests.post(url=self.base_url, params=self.base_parameters, headers=self.headers,
                          data=FacebookMessager.build_data(recipient_id=recipient_id, message=message))

        FacebookMessager.logger.info("Status Code: {} | Response: {}".format(r.status_code, r.json()))

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






