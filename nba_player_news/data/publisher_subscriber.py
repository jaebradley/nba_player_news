import os
import redis

from environment import REDIS_HOST, REDIS_PORT, REDIS_CHANNEL_NAME


class PublisherSubscriber:
    def __init__(self):
        self.redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)
        self.publisher_subscriber = self.redis_client.pubsub()

    def create_channel(self):
        self.publisher_subscriber.subscribe(REDIS_CHANNEL_NAME)