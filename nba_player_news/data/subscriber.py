import datetime
import json
import logging
import logging.config
import os

import redis

from environment import REDIS_URL, REDIS_CHANNEL_NAME
from nba_player_news.data.platform_subscriptions_publishers import EmailSubscriptionsPublisher, TwitterSubscriptionsPublisher


class Subscriber:
    logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "../../logger.conf"))
    logger = logging.getLogger("subscriber")

    def __init__(self):
        self.email_subscriptions_publisher = EmailSubscriptionsPublisher()
        self.twitter_subscriptions_publisher = TwitterSubscriptionsPublisher()
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)
        self.publisher_subscriber = self.redis_client.pubsub()
        self.publisher_subscriber.subscribe(REDIS_CHANNEL_NAME)

    def process_messages(self):
        Subscriber.logger.info("Started processing messages at {}".format(datetime.datetime.now()))

        while True:
            message = self.publisher_subscriber.get_message()
            if message and message["type"] == "message":
                self.process_message(message=message)

    def process_message(self, message):
        Subscriber.logger.info("Processing message with pattern: {pattern} | type: {type} | channel: {channel} | data: {data}".format(**message))
        # Goddamn rate limits
        # self.twitter_subscriptions_publisher.publish(message=json.loads(message["data"]))
        self.email_subscriptions_publisher.publish(message=json.loads(message["data"]))
