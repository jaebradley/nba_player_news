import datetime
import json
import logging
import logging.config
import os

import redis

from environment import REDIS_URL, REDIS_CHANNEL_NAME, REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME
from nba_player_news.data.platform_subscriptions_publishers import EmailSubscriptionsPublisher, TwitterSubscriptionsPublisher, FacebookMessengerSubscriptionsPublisher


class PlayerNewsSubscriber:
    logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "../../logger.conf"))
    logger = logging.getLogger("subscriber")

    def __init__(self):
        self.email_subscriptions_publisher = EmailSubscriptionsPublisher()
        self.twitter_subscriptions_publisher = TwitterSubscriptionsPublisher()
        self.facebook_messenger_subscriptions_publisher = FacebookMessengerSubscriptionsPublisher()
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)
        self.publisher_subscriber = self.redis_client.pubsub()
        self.publisher_subscriber.subscribe(REDIS_CHANNEL_NAME)

    def process_messages(self):
        PlayerNewsSubscriber.logger.info("Started processing messages at {}".format(datetime.datetime.now()))

        while True:
            message = self.publisher_subscriber.get_message()
            if message and message["type"] == "message":
                self.process_message(message=message)

    def process_message(self, message):
        PlayerNewsSubscriber.logger.info("Processing message with pattern: {pattern} | type: {type} | channel: {channel} | data: {data}".format(**message))
        # Goddamn rate limits
        # self.twitter_subscriptions_publisher.publish(message=json.loads(message["data"]))
        # Ugh spam
        # self.email_subscriptions_publisher.publish(message=json.loads(message["data"]))
        self.facebook_messenger_subscriptions_publisher.publish(message=json.loads(message["data"]))


class SubscriptionEventsSubscriber:
    logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "../../logger.conf"))
    logger = logging.getLogger("subscriber")

    def __init__(self):
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)
        self.publisher_subscriber = self.redis_client.pubsub()
        self.publisher_subscriber.subscribe(REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME)

    def process_messages(self):
        while True:
            message = self.publisher_subscriber.get_message()
            if message and message["type"] == "message":
                self.process_message(message=message)

    def process_message(self, message):
        if message.platform == "facebook":
            return