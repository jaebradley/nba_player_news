from nba_data import Client
import redis

class RotoWireInserter:

    def __init__(self):
        redis_client = redis.StrictRedis()

    def insert(self):
        for player_news_item in Client.get_player_news():


    @staticmethod
    def calculate_key_id(player_news_item):
        return "RotoWire" + "|" + unicode(player_news_item.source_id) + "|" \
               +  unicode(player_news_item.source_player_id) + "|" + unicode(player_news_item.source_update_id)
