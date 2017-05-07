import datetime
import json
import logging
import logging.config

import redis

from environment import REDIS_URL, REDIS_PLAYER_NEWS_CHANNEL_NAME, REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME, \
    REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME
from nba_player_news.data.message_builders import FacebookMessengerMessageBuilder
from nba_player_news.data.message_builders import FacebookSubscriberMessageBuilder
from nba_player_news.data.messages import SubscriptionMessage
from nba_player_news.data.senders import FacebookMessager
from nba_player_news.models import Subscription, SubscriptionAttempt, SubscriptionAttemptResult


class PlayerNewsSubscriber:
    logger = logging.getLogger("subscriber")

    def __init__(self):
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
        for subscription in Subscription.objects.filter(platform="facebook", unsubscribed_at=None):
            facebook_messages = FacebookMessengerMessageBuilder(message=message).build_messages()
            for facebook_message in facebook_messages:
                subscription_message = SubscriptionMessage(platform=subscription.platform,
                                                           platform_identifier=subscription.platform_identifier,
                                                           text=facebook_message)
                PlayerNewsSubscriber.logger.info("Publishing message: {} to subscription: {}"
                                                 .format(subscription_message.to_json(), subscription))
                subscriber_count = self.redis_client.publish(channel=REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME,
                                                             message=subscription_message.to_json())
                PlayerNewsSubscriber.logger.info("Publishing message: {} to channel: {} with {} subscribers"
                                                 .format(subscription_message.to_json(),
                                                         REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME,
                                                         subscriber_count))


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
        subscription = Subscription.objects.get(platform=message["platform"],
                                                platform_identifer=message["platform_identifier"])
        if message["platform"] == "facebook":
            PlayerNewsSubscriber.logger.info("Sending message: {} to user: {}".format(message["text"], message["platform_identifier"]))
            subscription_attempt = SubscriptionAttempt.objects.create(subscription=subscription, message=message["text"][:2048])
            response = self.facebook_messager.send(recipient_id=message["platform_identifier"], message=message["text"])
            successful = response.status_code == 200
            SubscriptionAttemptResult.objects.create(subscription_attempt=subscription_attempt, successful=successful,
                                                     response=response.json()[:2048])

        else:
            PlayerNewsSubscriber.logger.info("Unknown message: {}".format(message))