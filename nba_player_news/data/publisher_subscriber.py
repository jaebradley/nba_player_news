import os
import redis


class PublisherSubscriber:
    def __init__(self):
        self.redis_client = redis.StrictRedis(host=os.environ['REDIS_HOST'], port=os.environ['REDIS_PORT'], db=0)
        self.publisher_subscriber = self.redis_client.pubsub()

    def create_channel(self):
        self.publisher_subscriber.subscribe("nba_player_news")