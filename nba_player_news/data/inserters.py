import datetime
import json
import os

import pytz
import redis
from nba_data import Client


class RotoWireInserter:

    def __init__(self):
        self.redis_client = redis.StrictRedis(host=os.environ['REDIS_HOST'], port=os.environ['REDIS_PORT'], db=0)

    def insert(self):
        for player_news_item in Client.get_player_news():
            is_set = self.redis_client.setnx(name=RotoWireInserter.calculate_key_id(player_news_item=player_news_item),
                                             value=RotoWireInserter.to_json(player_news_item=player_news_item))

            if is_set:
                self.redis_client.publish(channel="nba_player_news",
                                          message=RotoWireInserter.to_json(player_news_item=player_news_item))

    @staticmethod
    def calculate_key_id(player_news_item):
        return "RotoWire:{p.source_id}:{p.source_player_id}:{p.source_update_id}".format(p=player_news_item)

    @staticmethod
    def to_json(player_news_item):
        return json.dumps({
            "caption": player_news_item.caption,
            "description": player_news_item.description,
            "published_at_unix_timestamp": RotoWireInserter.to_timestamp(value=player_news_item.published_at),
            "source_update_id": player_news_item.source_update_id,
            "source_id": player_news_item.source_id,
            "source_player_id": player_news_item.source_player_id,
            "first_name": player_news_item.first_name,
            "last_name": player_news_item.last_name,
            "position": player_news_item.position.name,
            "team": player_news_item.team.name,
            "priority": player_news_item.priority,
            "headline": player_news_item.headline,
            "injury": {
                "is_injured": player_news_item.injury.is_injured,
                "status": player_news_item.injury.status.name,
                "affected_area": player_news_item.injury.affected_area,
                "detail": player_news_item.injury.detail,
                "side": player_news_item.injury.side
            }
        })

    @staticmethod
    def to_timestamp(value):
        return (value - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds()
