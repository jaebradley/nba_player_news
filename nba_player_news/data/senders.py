import logging
import logging.config
import os
import tweepy

import yagmail

from environment import GMAIL_PASSWORD, GMAIL_USERNAME, TWITTER_ACCESS_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET
from nba_player_news.data.sent_message_builders import EmailMessageBuilder


class Emailer:
    logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "../../logger.conf"))
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
    logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "../../logger.conf"))
    logger = logging.getLogger("tweeter")

    def __init__(self):
        self.client = tweepy.API(tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
                                       .set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET))

    def send(self, username, message):
        self.client.send_direct_message(username, message)

