import json
import logging
import logging.config
import os

import redis
import tweepy

from environment import REDIS_URL, REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME
from environment import TWITTER_ACCESS_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET
from nba_player_news.data.messages import SubscriptionMessage
from nba_player_news.data.senders import Emailer, Tweeter
from nba_player_news.data.sent_message_builders import FacebookMessengerMessageBuilder
from nba_player_news.models import Subscription


class EmailSubscriptionsPublisher:
    logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "../../logger.conf"))
    logger = logging.getLogger("emailSubscriptionsPublisher")

    def __init__(self):
        self.emailer = Emailer()

    def publish(self, message):
        for subscription in Subscription.objects.filter(platform="email", unsubscribed_at=None):
            EmailSubscriptionsPublisher.logger.info("Publishing message: {} to subscription: {}".format(message, subscription))
            self.emailer.send(destination=subscription.platform_identifier, message=message)


class TwitterSubscriptionsPublisher:
    logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "../../logger.conf"))
    logger = logging.getLogger("twitterSubscriptionsPublisher")

    def __init__(self):

        auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
        auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
        self.client = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)
        self.tweeter = Tweeter()

    def publish(self, message):
        for page in tweepy.Cursor(self.client.followers_ids, id="nba_player_news", count=200).pages():
            for follower_id in page:
                TwitterSubscriptionsPublisher.logger.info("Publishing message: {} to follower: {}".format(message, follower_id))
                self.tweeter.send(user_id=follower_id, message=message)


class FacebookMessengerSubscriptionsPublisher:
    logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "../../logger.conf"))
    logger = logging.getLogger("facebookSubscriptionsPublisher")

    def __init__(self):
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)

    def publish(self, message):
        for subscription in Subscription.objects.filter(platform="facebook", unsubscribed_at=None):
            FacebookMessengerSubscriptionsPublisher.logger.info("Publishing message: {} to subscription: {}".format(message, subscription))
            message_text = FacebookMessengerMessageBuilder(message=message).build()
            subscription_message = SubscriptionMessage(platform=subscription.platform, platform_identifier=subscription.platform_identifier, text=message_text)
            self.redis_client.publish(channel=REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME, message=json.dumps(subscription_message))

