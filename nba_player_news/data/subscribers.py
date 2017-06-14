import datetime
import json
import logging
import logging.config

import redis

from environment import REDIS_URL, REDIS_PLAYER_NEWS_CHANNEL_NAME, REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME, \
    REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME
from nba_player_news.data.publishers import PlayerNewsSubscriptionsMessagesPublisher
from nba_player_news.data.senders import FacebookMessager
from nba_player_news.data.subscriber_event.processors import FacebookSubscriberEventProcessor
from nba_player_news.models import Subscription, SubscriptionAttempt, SubscriptionAttemptResult


class BaseSubscriber:
    logger = logging.getLogger("subscriber")

    def __init__(self, subscription_channel_name):
        self.subscription_channel_name = subscription_channel_name
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)
        self.publisher_subscriber = self.redis_client.pubsub()

    def process_messages(self):
        self.publisher_subscriber.subscribe(self.subscription_channel_name)
        BaseSubscriber.logger.info("Started processing messages at {now}".format(now=datetime.datetime.now()))

        while True:
            message = self.publisher_subscriber.get_message()
            if message and message["type"] == "message":
                BaseSubscriber.logger.info("Processing message: {message}".format(message=message))
                try:
                    self.process_message(message=json.loads(message["data"]))
                except BaseException as e:
                    # Catch all exceptions so subscriber doesn't die
                    BaseSubscriber.logger.error(e.message)

    def process_message(self, message):
        raise NotImplementedError()


class PlayerNewsSubscriber(BaseSubscriber):

    def __init__(self):
        self.player_news_subscriptions_messages_publisher = PlayerNewsSubscriptionsMessagesPublisher()
        BaseSubscriber.__init__(self, REDIS_PLAYER_NEWS_CHANNEL_NAME)

    def process_message(self, message):
        self.player_news_subscriptions_messages_publisher.publish(player_news=message)


class SubscriberEventsSubscriber(BaseSubscriber):

    def __init__(self):
        self.facebook_subscriber_event_processor = FacebookSubscriberEventProcessor()
        BaseSubscriber.__init__(self, REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME)

    def process_message(self, message):
        if message["platform"] == "facebook":
            self.facebook_subscriber_event_processor.process(subscriber_event_message=message)
        else:
            PlayerNewsSubscriber.logger.info("Unknown message: {message}".format(message=message))


class SubscriptionMessagesSubscriber(BaseSubscriber):

    def __init__(self):
        self.facebook_messager = FacebookMessager()
        BaseSubscriber.__init__(self, REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME)

    def process_message(self, message):
        subscription = Subscription.objects.get(platform=message["platform"],
                                                platform_identifier=message["platform_identifier"])
        if message["platform"] == "facebook":
            PlayerNewsSubscriber.logger.info("Sending message: {message} to user: {user}"
                                             .format(message=message["text"], user=message["platform_identifier"]))
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
        self.facebook_subscriber_event_processor = FacebookSubscriberEventProcessor()
        self.facebook_messager = FacebookMessager()
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)
        self.player_news_publisher_subscriber = self.redis_client.pubsub()
        self.subscriber_events_publisher_subscriber = self.redis_client.pubsub()
        self.subscription_messages_publisher_subscriber = self.redis_client.pubsub()
        self.player_news_publisher_subscriber.subscribe(REDIS_PLAYER_NEWS_CHANNEL_NAME)
        self.subscriber_events_publisher_subscriber.subscribe(REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME)
        self.subscription_messages_publisher_subscriber.subscribe(REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME)
        self.player_news_subscriptions_messages_publisher = PlayerNewsSubscriptionsMessagesPublisher()

    def process_messages(self):
        AllSubscribers.logger.info("Started subscribing to all messages at {now}".format(now=datetime.datetime.now()))

        while True:
            # Process player news
            player_news_message = self.player_news_publisher_subscriber.get_message()
            if player_news_message and player_news_message["type"] == "message":
                try:
                    self.player_news_subscriptions_messages_publisher.publish(player_news=json.loads(player_news_message["data"]))
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

    def process_subscriber_message(self, message):
        if message["platform"] == "facebook":
            self.facebook_subscriber_event_processor.process(subscriber_event_message=message)
        else:
            AllSubscribers.logger.info("Unknown message: {}".format(message))

    def process_subscription_message(self, message):
        subscription = Subscription.objects.get(platform=message["platform"],
                                                platform_identifier=message["platform_identifier"])
        if message["platform"] == "facebook":
            AllSubscribers.logger.info("Sending message: {message} to user: {user}".format(message=message["text"],
                                                                                           user=message["platform_identifier"]))
            subscription_attempt = SubscriptionAttempt.objects.create(subscription=subscription, message=message["text"][:2048])
            response = self.facebook_messager.send(recipient_id=message["platform_identifier"], message=message["text"])
            successful = response.status_code == 200
            SubscriptionAttemptResult.objects.create(subscription_attempt=subscription_attempt, successful=successful,
                                                     response=response.text[:2048])

        else:
            PlayerNewsSubscriber.logger.info("Unknown message: {}".format(message))