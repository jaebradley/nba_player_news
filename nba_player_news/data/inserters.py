import json
import os
from nba_data import Client
import redis


class RotoWireInserter:

    def __init__(self):
        self.redis_client = redis.StrictRedis(host=os.environ['REDIS_HOST'], port=os.environ['REDIS_PORT'], db=0)

    def insert(self):
        for player_news_item in Client.get_player_news():
            self.redis_client.set(name=RotoWireInserter.calculate_key_id(player_news_item=player_news_item),
                                  value=json.dumps(player_news_item))

    @staticmethod
    def calculate_key_id(player_news_item):
        return "Rotowire:{p.source_id}:{p.source_player_id}:{p.source_update_id}".format(p=player_news_item)
