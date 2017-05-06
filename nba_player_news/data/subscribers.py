import datetime
import json
import logging
import logging.config

import redis

from environment import REDIS_URL, REDIS_PLAYER_NEWS_CHANNEL_NAME, REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME, \
    REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME
from nba_player_news.data.publishers import FacebookMessengerSubscriptionsPublisher
from nba_player_news.data.senders import FacebookMessager
from nba_player_news.data.message_builders import FacebookSubscriberMessageBuilder


class PlayerNewsSubscriber:
    logger = logging.getLogger("subscriber")

    def __init__(self):
        self.facebook_messenger_subscriptions_publisher = FacebookMessengerSubscriptionsPublisher()
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)
        self.publisher_subscriber = self.redis_client.pubsub()
        self.publisher_subscriber.subscribe(REDIS_PLAYER_NEWS_CHANNEL_NAME)

    def process_messages(self):
        PlayerNewsSubscriber.logger.info("Started processing player news messages at {}".format(datetime.datetime.now()))

        while True:
            message = self.publisher_subscriber.get_message()
            if message and message["type"] == "message":
                PlayerNewsSubscriber.logger.info("Processing player news message: {}".format(message))
                self.process_message(message=json.loads(message["data"]))

    def process_message(self, message):
        self.facebook_messenger_subscriptions_publisher.publish(message=message)


class SubscriberEventsSubscriber:
    logger = logging.getLogger("subscriber")

    def __init__(self):
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)
        self.publisher_subscriber = self.redis_client.pubsub()
        self.publisher_subscriber.subscribe(REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME)

    def process_messages(self):
        PlayerNewsSubscriber.logger.info("Started processing messages at {}".format(datetime.datetime.now()))

        while True:
            message = self.publisher_subscriber.get_message()
            if message and message["type"] == "message":
                PlayerNewsSubscriber.logger.info("Processing subscriber message: {}".format(message))
                self.process_message(message=json.loads(message["data"]))

    def process_message(self, message):
        if message["platform"] == "facebook":
            subscription_message = FacebookSubscriberMessageBuilder(event_data=message).build()
            subscriber_count = self.redis_client.publish(channel=REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME,
                                                         message=subscription_message.to_json())
            PlayerNewsSubscriber.logger.info("Publishing subscriber message: {} to channel: {} with {} subscribers"
                                             .format(subscription_message, REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME,
                                                     subscriber_count))
        else:
            PlayerNewsSubscriber.logger.info("Unknown message: {}".format(message))


class SubscriptionMessagesSubscriber:
    logger = logging.getLogger("subscriber")

    def __init__(self):
        self.facebook_messager = FacebookMessager()
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)
        self.publisher_subscriber = self.redis_client.pubsub()
        self.publisher_subscriber.subscribe(REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME)

    def process_messages(self):
        PlayerNewsSubscriber.logger.info("Started processing messages at {}".format(datetime.datetime.now()))

        while True:
            message = self.publisher_subscriber.get_message()
            if message and message["type"] == "message":
                PlayerNewsSubscriber.logger.info("Processing subscription message: {}".format(message))
                self.process_message(message=json.loads(message["data"]))

    def process_message(self, message):
        if message["platform"] == "facebook":
            PlayerNewsSubscriber.logger.info("Sending message: {} to user: {}".format(message["text"], message["platform_identifier"]))
            self.facebook_messager.send(recipient_id=message["platform_identifier"], message=message["text"])
        else:
            PlayerNewsSubscriber.logger.info("Unknown message: {}".format(message))