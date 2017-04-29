import os
from nba_data import Client
import redis


class RotoWireInserter:

    def __init__(self):
        self.redis_client = redis.StrictRedis(host=os.environ['REDIS_HOST'], port=os.environ['REDIS_PORT'], db=0)

    def insert(self):
        for player_news_item in Client.get_player_news():
            self.redis_client.set(name=RotoWireInserter.calculate_key_id(player_news_item=player_news_item),
                                  value=player_news_item)

    @staticmethod
    def calculate_key_id(player_news_item):
        return "RotoWire" + "|" + unicode(player_news_item.source_id) + "|" \
               +  unicode(player_news_item.source_player_id) + "|" + unicode(player_news_item.source_update_id)
