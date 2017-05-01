import json
import logging
import logging.config
import os

import redis

from environment import REDIS_HOST, REDIS_PORT, REDIS_CHANNEL_NAME
from nba_player_news.data.platform_subscriptions_publishers import EmailSubscriptionsPublisher


class Subscriber:
    logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "../../logger.conf"))
    logger = logging.getLogger("subscriber")

    def __init__(self):
        self.email_subscriptions_publisher = EmailSubscriptionsPublisher()
        self.redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)
        self.publisher_subscriber = self.redis_client.pubsub()
        self.publisher_subscriber.subscribe(REDIS_CHANNEL_NAME)

    def process_messages(self):
        while True:
            message = self.publisher_subscriber.get_message()
            if message:
                self.process_message(message=message)

    def process_message(self, message):
        Subscriber.logger.info("Processing message with pattern: {pattern} | type: {type} | channel: {channel} | data: {data}".format(**message))
        self.email_subscriptions_publisher.publish(message=json.loads(message))
