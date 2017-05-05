import datetime
import json
import logging
import logging.config
import os

import redis

from environment import REDIS_URL, REDIS_PLAYER_NEWS_CHANNEL_NAME, REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME, REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME
from nba_player_news.data.platform_subscriptions_publishers import FacebookMessengerSubscriptionsPublisher
from nba_player_news.data.senders import FacebookMessager
from nba_player_news.data.subscriber_event_processors import FacebookSubscriberEventsProcessor


class PlayerNewsSubscriber:
    logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "../../logger.conf"))
    logger = logging.getLogger("subscriber")

    def __init__(self):
        self.facebook_messenger_subscriptions_publisher = FacebookMessengerSubscriptionsPublisher()
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)
        self.publisher_subscriber = self.redis_client.pubsub()
        self.publisher_subscriber.subscribe(REDIS_PLAYER_NEWS_CHANNEL_NAME)

    def process_messages(self):
        PlayerNewsSubscriber.logger.info("Started processing messages at {}".format(datetime.datetime.now()))

        while True:
            message = self.publisher_subscriber.get_message()
            if message and message["type"] == "message":
                self.process_message(message=json.loads(message["data"]))

    def process_message(self, message):
        PlayerNewsSubscriber.logger.info("Processing message with pattern: {pattern} | type: {type} | channel: {channel} | data: {data}".format(**message))
        self.facebook_messenger_subscriptions_publisher.publish(message=message)


class SubscriberEventsSubscriber:
    logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "../../logger.conf"))
    logger = logging.getLogger("subscriber")

    def __init__(self):
        self.facebook_subscriber_events_processor = FacebookSubscriberEventsProcessor()
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
            subscription_message = self.facebook_subscriber_events_processor.process(event_data=json.loads(message))
            self.redis_client.publish(channel=REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME, message=subscription_message)
        else:
            SubscriberEventsSubscriber.logger.info("Unknown message: {}".format(message))


class SubscriptionEventsSubscriber:
    def __init__(self):
        self.facebook_subscriber_events_processor = FacebookSubscriberEventsProcessor()
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)
        self.publisher_subscriber = self.redis_client.pubsub()
        self.publisher_subscriber.subscribe(REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME)

    def process_messages(self):
        while True:
            message = self.publisher_subscriber.get_message()
            if message and message["type"] == "message":
                self.process_message(message=json.loads(message))

    def process_message(self, message):
        if message.platform == "facebook":
            subscription_message = self.facebook_subscriber_events_processor.process(event_data=message)
            self.redis_client.publish(channel=REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME, message=json.dumps(subscription_message))
        else:
            SubscriberEventsSubscriber.logger.info("Unknown message: {}".format(message))


class SubscriptionMessagesSubscriber:
    logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "../../logger.conf"))
    logger = logging.getLogger("subscriber")

    def __init__(self):
        self.facebook_messager = FacebookMessager()
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)
        self.publisher_subscriber = self.redis_client.pubsub()
        self.publisher_subscriber.subscribe(REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME)

    def process_messages(self):
        SubscriptionMessagesSubscriber.logger.info("Started processing messages at {}".format(datetime.datetime.now()))

        while True:
            message = self.publisher_subscriber.get_message()
            if message and message["type"] == "message":
                self.process_message(message=json.loads(message))

    def process_message(self, message):
        SubscriptionMessagesSubscriber.logger.info("Processing message with pattern: {pattern} | type: {type} | channel: {channel} | data: {data}".format(**message))
        if message.platform == "facebook":
            self.facebook_messager.send(recipient_id=message.platform_id, message=message.text)