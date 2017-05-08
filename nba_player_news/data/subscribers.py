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


class BaseSubscriber:
    logger = logging.getLogger("subscriber")

    def __init__(self, subscription_channel_name):
        self.subscription_channel_name = subscription_channel_name
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)
        self.publisher_subscriber = self.redis_client.pubsub()
        self.publisher_subscriber.subscribe(self.subscription_channel_name)

    def process_messages(self):
        BaseSubscriber.logger.info("Started processing messages at {now}".format(now=datetime.datetime.now()))

        while True:
            message = self.publisher_subscriber.get_message()
            if message and message["type"] == "message":
                BaseSubscriber.logger.info("Processing message: {}".format(message))
                try:
                    self.process_message(message=json.loads(message["data"]))
                except BaseException as e:
                    # Catch all exceptions so subscriber doesn't die
                    BaseSubscriber.logger.error(e.message)

    def process_message(self, message):
        raise NotImplementedError()


class PlayerNewsSubscriber(BaseSubscriber):

    def __init__(self):
        BaseSubscriber.__init__(self, REDIS_PLAYER_NEWS_CHANNEL_NAME)

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


class SubscriberEventsSubscriber(BaseSubscriber):

    def __init__(self):
        BaseSubscriber.__init__(self, REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME)

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


class SubscriptionMessagesSubscriber(BaseSubscriber):

    def __init__(self):
        self.facebook_messager = FacebookMessager()
        BaseSubscriber.__init__(self, REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME)

    def process_message(self, message):
        subscription = Subscription.objects.get(platform=message["platform"],
                                                platform_identifier=message["platform_identifier"])
        if message["platform"] == "facebook":
            PlayerNewsSubscriber.logger.info("Sending message: {message} to user: {user}".format(message=message["text"],
                                                                                                 user=message["platform_identifier"]))
            subscription_attempt = SubscriptionAttempt.objects.create(subscription=subscription, message=message["text"][:2048])
            response = self.facebook_messager.send(recipient_id=message["platform_identifier"], message=message["text"])
            successful = response.status_code == 200
            SubscriptionAttemptResult.objects.create(subscription_attempt=subscription_attempt, successful=successful,
                                                     response=response.text[:2048])

        else:
            PlayerNewsSubscriber.logger.info("Unknown message: {}".format(message))


class AllSubscribers:
    # Helper class for saving money on Heroku
    # Contains a lot of duplicate logic
    logger = logging.getLogger("subscriber")

    def __init__(self):
        self.facebook_messager = FacebookMessager()
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)
        self.player_news_publisher_subscriber = self.redis_client.pubsub()
        self.subscriber_events_publisher_subscriber = self.redis_client.pubsub()
        self.subscription_messages_publisher_subscriber = self.redis_client.pubsub()
        self.player_news_publisher_subscriber.subscribe(REDIS_PLAYER_NEWS_CHANNEL_NAME)
        self.subscriber_events_publisher_subscriber.subscribe(REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME)
        self.subscription_messages_publisher_subscriber.subscribe(REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME)

    def process_messages(self):
        AllSubscribers.logger.info("Started subscribing to all messages at {now}".format(now=datetime.datetime.now()))

        while True:
            # Process player news
            player_news_message = self.player_news_publisher_subscriber.get_message()
            if player_news_message and player_news_message["type"] == "message":
                try:
                    self.process_player_news_message(message=json.loads(player_news_message["data"]))
                except BaseException as e:
                    # Catch all exceptions so subscriber doesn't die
                    AllSubscribers.logger.error(e.message)

            # Process subscriber events
            subscriber_event_message = self.subscriber_events_publisher_subscriber.get_message()
            if subscriber_event_message and subscriber_event_message["type"] == "message":
                try:
                    self.process_subscriber_message(message=json.loads(subscriber_event_message["data"]))
                except BaseException as e:
                    # Catch all exceptions so subscriber doesn't die
                    AllSubscribers.logger.error(e.message)

            # Process subscription events
            subscription_event_message = self.subscription_messages_publisher_subscriber.get_message()
            if subscription_event_message and subscription_event_message["type"] == "message":
                try:
                    self.process_subscription_message(message=json.loads(subscription_event_message["data"]))
                except BaseException as e:
                    # Catch all exceptions so subscriber doesn't die
                    AllSubscribers.logger.error(e.message)

    def process_player_news_message(self, message):
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

    def process_subscriber_message(self, message):
        if message["platform"] == "facebook":
            subscription_message = FacebookSubscriberMessageBuilder(event_data=message).build()
            subscriber_count = self.redis_client.publish(channel=REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME,
                                                         message=subscription_message.to_json())
            PlayerNewsSubscriber.logger.info("Publishing subscriber message: {} to channel: {} with {} subscribers"
                                             .format(subscription_message, REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME,
                                                     subscriber_count))
        else:
            PlayerNewsSubscriber.logger.info("Unknown message: {}".format(message))

    def process_subscription_message(self, message):
        subscription = Subscription.objects.get(platform=message["platform"],
                                                platform_identifier=message["platform_identifier"])
        if message["platform"] == "facebook":
            PlayerNewsSubscriber.logger.info("Sending message: {message} to user: {user}".format(message=message["text"],
                                                                                                 user=message["platform_identifier"]))
            subscription_attempt = SubscriptionAttempt.objects.create(subscription=subscription, message=message["text"][:2048])
            response = self.facebook_messager.send(recipient_id=message["platform_identifier"], message=message["text"])
            successful = response.status_code == 200
            SubscriptionAttemptResult.objects.create(subscription_attempt=subscription_attempt, successful=successful,
                                                     response=response.text[:2048])

        else:
            PlayerNewsSubscriber.logger.info("Unknown message: {}".format(message))