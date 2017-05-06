import datetime
import json
import logging
import logging.config

import redis

from environment import REDIS_URL, REDIS_PLAYER_NEWS_CHANNEL_NAME, REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME, \
    REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME
from nba_player_news.data.platform_subscriptions_publishers import FacebookMessengerSubscriptionsPublisher
from nba_player_news.data.senders import FacebookMessager
from nba_player_news.data.subscriber_event_processors import FacebookSubscriberEventsProcessor

logger = logging.getLogger("subscriber")


class PlayerNewsSubscriber:

    def __init__(self):
        self.facebook_messenger_subscriptions_publisher = FacebookMessengerSubscriptionsPublisher()
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)
        self.publisher_subscriber = self.redis_client.pubsub()
        self.publisher_subscriber.subscribe(REDIS_PLAYER_NEWS_CHANNEL_NAME)

    def process_messages(self):
        logger.info("Started processing messages at {}".format(datetime.datetime.now()))

        while True:
            message = self.publisher_subscriber.get_message()
            if message and message["type"] == "message":
                logger.info("Processing player news message: {}".format(message))
                self.process_message(message=json.loads(message["data"]))

    def process_message(self, message):
        self.facebook_messenger_subscriptions_publisher.publish(message=message)


class SubscriberEventsSubscriber:

    def __init__(self):
        self.facebook_subscriber_events_processor = FacebookSubscriberEventsProcessor()
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)
        self.publisher_subscriber = self.redis_client.pubsub()
        self.publisher_subscriber.subscribe(REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME)

    def process_messages(self):
        logger.info("Started processing messages at {}".format(datetime.datetime.now()))

        while True:
            message = self.publisher_subscriber.get_message()
            if message and message["type"] == "message":
                logger.info("Processing subscriber message: {}".format(message))
                self.process_message(message=json.loads(message["data"]))

    def process_message(self, message):
        if message["platform"] == "facebook":
            subscription_message = self.facebook_subscriber_events_processor.process(event_data=message)
            subscriber_count = self.redis_client.publish(channel=REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME,
                                                         message=subscription_message.to_json())
            logger.info("Publishing subscriber message: {} to channel: {} with {} subscribers"
                        .format(subscription_message, REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME, subscriber_count))
        else:
            logger.info("Unknown message: {}".format(message))


class SubscriptionMessagesSubscriber:

    def __init__(self):
        self.facebook_messager = FacebookMessager()
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)
        self.publisher_subscriber = self.redis_client.pubsub()
        self.publisher_subscriber.subscribe(REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME)

    def process_messages(self):
        logger.info("Started processing messages at {}".format(datetime.datetime.now()))

        while True:
            message = self.publisher_subscriber.get_message()
            if message and message["type"] == "message":
                logger.info("Processing subscription message: {}".format(message))
                self.process_message(message=json.loads(message["data"]))

    def process_message(self, message):
        if message["platform"] == "facebook":
            logger.info("Sending message: {} to user: {}".format(message["text"], message["platform_identifer"]))
            self.facebook_messager.send(recipient_id=message["platform_identifier"], message=message["text"])
        else:
            logger.info("Unknown message: {}".format(message))