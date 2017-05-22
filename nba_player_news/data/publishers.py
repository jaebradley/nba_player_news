# -*- coding: utf-8 -*-

import datetime
import json
import logging
import logging.config

import pytz
import redis
import tweepy
from nba_data import Client
from unidecode import unidecode

from environment import REDIS_PLAYER_NEWS_CHANNEL_NAME, REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME
from environment import REDIS_URL
from environment import TWITTER_ACCESS_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET
from nba_player_news.data.messages import SubscriptionMessage
from nba_player_news.data.senders import Emailer, Tweeter
from nba_player_news.models import Subscription
from nba_player_news.data.message_builders import FacebookMessengerMessageBuilder


class RotoWirePlayerNewsPublisher:
    logger = logging.getLogger("publisher")

    def __init__(self):
        self.redis_client = redis.StrictRedis.from_url(url=REDIS_URL)

    def publish(self):
        for player_news_item in Client.get_player_news():
            value = RotoWirePlayerNewsPublisher.to_json(player_news_item=player_news_item)

            RotoWirePlayerNewsPublisher.logger.info("Inserting player news item: {}".format(value))
            was_set = self.redis_client.setnx(name=RotoWirePlayerNewsPublisher.calculate_key(player_news_item=player_news_item),
                                              value=value)
            RotoWirePlayerNewsPublisher.logger.info("Inserted player news item: {} | was set: {}".format(value, was_set))

            if was_set:
                RotoWirePlayerNewsPublisher.logger.info("Publishing player news item: {} to channel {}"
                                                        .format(value, REDIS_PLAYER_NEWS_CHANNEL_NAME))
                subscriber_count = self.redis_client.publish(channel=REDIS_PLAYER_NEWS_CHANNEL_NAME, message=value)
                RotoWirePlayerNewsPublisher.logger.info("Published player news item: {} to channel {} with {} subscribers"
                                                        .format(value, REDIS_PLAYER_NEWS_CHANNEL_NAME, subscriber_count))

    @staticmethod
    def calculate_key(player_news_item):
        return "RotoWire:{p.source_id}:{p.source_player_id}:{p.source_update_id}".format(p=player_news_item)

    @staticmethod
    def to_json(player_news_item):
        RotoWirePlayerNewsPublisher.logger.info("JSONifying Player News Item: {}", player_news_item)
        return json.dumps({
            "caption": unidecode(unicode(player_news_item.caption)),
            "description": unidecode(unicode(player_news_item.description)),
            "published_at_unix_timestamp": RotoWirePlayerNewsPublisher.to_timestamp(value=player_news_item.published_at),
            "source_update_id": player_news_item.source_update_id,
            "source_id": player_news_item.source_id,
            "source_player_id": player_news_item.source_player_id,
            "first_name": unidecode(unicode(player_news_item.first_name)),
            "last_name": unidecode(unicode(player_news_item.last_name)),
            "position": player_news_item.position.value,
            "team": player_news_item.team.value,
            "priority": player_news_item.priority,
            "headline": unidecode(unicode(player_news_item.headline)),
            "injury": {
                "is_injured": player_news_item.injury.is_injured,
                "status": "Unknown" if player_news_item.injury.status is None else player_news_item.injury.status.value,
                "affected_area": unidecode(unicode(player_news_item.injury.affected_area)),
                "detail": unidecode(unicode(player_news_item.injury.detail)),
                "side": unidecode(unicode(player_news_item.injury.side))
            }
        })

    @staticmethod
    def to_timestamp(value):
        return (value - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds()


class PlayerNewsSubscriptionsMessagesPublisher:
    logger = logging.getLogger("publisher")

    def __init__(self):
        self.subscription_message_publisher = PlayerNewsSubscriptionMessagePublisher()

    def publish(self, player_news):
        for subscription in Subscription.objects.filter(unsubscribed_at=None):
            messages = self.build_messages(subscription=subscription, player_news=player_news)
            for message in messages:
                self.subscription_message_publisher.publish(subscription=subscription, message=message)
                PlayerNewsSubscriptionsMessagesPublisher.logger("Published to {subscription}: {message}"
                                                                .format(subscription=subscription, message=message))

    def build_messages(self, subscription, player_news):
        if subscription.platform == "facebook":
            return FacebookMessengerMessageBuilder(message=player_news).build_messages()

        raise RuntimeError("Cannot build messages for platform: {platform}".format(platform=subscription.platform))


class PlayerNewsSubscriptionMessagePublisher:
    logger = logging.getLogger("publisher")

    def __init__(self):
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)
        self.channel = REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME

    def publish(self, subscription, message):
        subscription_message = SubscriptionMessage(platform=subscription.platform,
                                                   platform_identifier=subscription.platform_identifier,
                                                   text=message)
        subscriber_count = self.redis_client.publish(channel=self.channel, message=subscription_message.to_json())

        PlayerNewsSubscriptionMessagePublisher.logger.info("Published to {subscriber_count} subscribers: {message}"
                                                           .format(subscriber_count=subscriber_count,
                                                                   message=subscription_message.to_json()))
