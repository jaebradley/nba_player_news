# -*- coding: utf-8 -*-

import datetime
import json
import logging
import logging.config
import os

import pytz
import redis
from nba_data import Client
from unidecode import unidecode

from environment import REDIS_HOST, REDIS_PORT, REDIS_CHANNEL_NAME


class RotoWireInserter:
    logging.config.fileConfig(os.path.join(os.path.dirname(__file__), '../../logger.conf'))
    logger = logging.getLogger('inserter')

    def __init__(self):
        self.redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    def insert(self):
        for player_news_item in Client.get_player_news():
            value = RotoWireInserter.to_json(player_news_item=player_news_item)

            RotoWireInserter.logger.info("Inserting player news item: {}".format(value))
            was_set = self.redis_client.setnx(name=RotoWireInserter.calculate_key(player_news_item=player_news_item),
                                              value=value)
            RotoWireInserter.logger.info("Inserted player news item: {} | was set: {}".format(value, was_set))

            if was_set:
                RotoWireInserter.logger.info("Publishing player news item: {} to channel {}".format(value, REDIS_CHANNEL_NAME))
                subscriber_count = self.redis_client.publish(channel=REDIS_CHANNEL_NAME, message=value)
                RotoWireInserter.logger.info("Published player news item: {} to channel {} with {} subscribers".format(value, REDIS_CHANNEL_NAME, subscriber_count))

    @staticmethod
    def calculate_key(player_news_item):
        return "RotoWire:{p.source_id}:{p.source_player_id}:{p.source_update_id}".format(p=player_news_item)

    @staticmethod
    def to_json(player_news_item):
        print player_news_item.__dict__
        return json.dumps({
            "caption": unidecode(unicode(player_news_item.caption)),
            "description": unidecode(unicode(player_news_item.description)),
            "published_at_unix_timestamp": RotoWireInserter.to_timestamp(value=player_news_item.published_at),
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
                "status": player_news_item.injury.status.value,
                "affected_area": unidecode(unicode(player_news_item.injury.affected_area)),
                "detail": unidecode(unicode(player_news_item.injury.detail)),
                "side": unidecode(unicode(player_news_item.injury.side))
            }
        })

    @staticmethod
    def to_timestamp(value):
        return (value - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds()
