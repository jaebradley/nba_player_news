from unittest import TestCase

from mock import Mock, patch

from environment import REDIS_PLAYER_NEWS_CHANNEL_NAME
from nba_player_news.data.publishers import RotoWirePlayerNewsPublisher


class MockPlayerNewsItemForKeyCalculation:
    def __init__(self, source_id, source_player_id, source_update_id):
        self.source_id = source_id
        self.source_player_id = source_player_id
        self.source_update_id = source_update_id


class MockValue:
    def __init__(self, value):
        self.value = value


class MockPlayerNewsItemInjury:
    def __init__(self, is_injured, status, affected_area, detail, side):
        self.is_injured = is_injured
        self.status = status
        self.affected_area = affected_area
        self.detail = detail
        self.side = side


class MockPlayerNewsItem:
    def __init__(self, caption, description, published_at, source_update_id, source_id, source_player_id,
                 first_name, last_name, position, team, priority, headline, injury):
        self.caption = caption
        self.description = description
        self.published_at = published_at
        self.source_update_id = source_update_id
        self.source_id = source_id
        self.source_player_id = source_player_id
        self.first_name = first_name
        self.last_name = last_name
        self.position = position
        self.team = team
        self.priority = priority
        self.headline = headline
        self.injury = injury


def forward_value(value):
    return value


class TestRotoWirePlayerNewsPublisher(TestCase):
    publisher = RotoWirePlayerNewsPublisher()

    def test_key_calculation(self):
        player_news_item = MockPlayerNewsItemForKeyCalculation(source_id="foo", source_player_id="bar",
                                                               source_update_id="baz")
        expected = "RotoWire:foo:bar:baz"
        self.assertEqual(RotoWirePlayerNewsPublisher.calculate_key(player_news_item=player_news_item), expected)

    @patch("json.dumps", side_effect=forward_value)
    def test_jsonification(self, mocked_json_dumps):
        caption = "caption"
        description = "description"
        published_at = 1
        source_update_id = "source update id"
        source_id = "source id"
        source_player_id = "source player id"
        first_name = "first name"
        last_name = "last name"
        position_value = "position"
        position = MockValue(value=position_value)
        team_value = "team"
        team = MockValue(value=team_value)
        priority = "priority"
        headline = "headline"
        is_injured = "is injured"
        injury_status_value = "status"
        injury_status = MockValue(value=injury_status_value)
        affected_area = "affected area"
        detail = "detail"
        side = "side"
        injury = MockPlayerNewsItemInjury(is_injured=is_injured, status=injury_status, affected_area=affected_area,
                                          detail=detail, side=side)

        player_news_item = MockPlayerNewsItem(caption=caption, description=description, published_at=published_at,
                                              source_update_id=source_update_id, source_id=source_id,
                                              source_player_id=source_player_id, first_name=first_name,
                                              last_name=last_name, position=position, team=team,
                                              priority=priority, headline=headline, injury=injury)
        converted_player_news_item = {
            "caption": "caption",
            "description": "description",
            "source_update_id": "source update id",
            "source_player_id": "source player id",
            "first_name": "first name",
            "last_name": "last name",
            "position": "position",
            "team": "team",
            "source_id": "source id",
            "priority": "priority",
            "headline": "headline",
            "injury": {
              "is_injured": "is injured",
              "status": "status",
              "affected_area": "affected area",
              "detail": "detail",
              "side": "side"
            }
        }

        jsonified_player_news = RotoWirePlayerNewsPublisher.to_json(player_news_item=player_news_item)

        mocked_json_dumps.assert_called_once_with(converted_player_news_item)

        self.assertEqual(jsonified_player_news, converted_player_news_item)

    @patch("nba_data.Client.get_player_news")
    @patch("nba_player_news.data.publishers.RotoWirePlayerNewsPublisher.calculate_key")
    @patch("nba_player_news.data.publishers.RotoWirePlayerNewsPublisher.to_json")
    def test_publish_when_not_set(self, mocked_to_json, mocked_key_calculation, mocked_get_player_news):
        mocked_get_player_news.return_value = ["foo"]
        mocked_to_json.return_value = "baz"
        mocked_key_calculation.return_value = "bar"
        self.publisher.redis_client.setnx = Mock("redis_client_setter")
        self.publisher.redis_client.setnx.return_value = False
        self.publisher.redis_client.publish = Mock("redis_client_publish")

        self.publisher.publish()

        mocked_get_player_news.assert_called_once()
        mocked_to_json.assert_called_once_with(player_news_item="foo")
        mocked_key_calculation.assert_called_once_with(player_news_item="foo")
        self.publisher.redis_client.setnx.assert_called_once_with(name="bar", value="baz")
        self.assertFalse(self.publisher.redis_client.publish.called)

    @patch("nba_data.Client.get_player_news")
    @patch("nba_player_news.data.publishers.RotoWirePlayerNewsPublisher.calculate_key")
    @patch("nba_player_news.data.publishers.RotoWirePlayerNewsPublisher.to_json")
    def test_publish_when_set(self, mocked_to_json, mocked_key_calculation, mocked_get_player_news):
        mocked_get_player_news.return_value = ["foo"]
        mocked_to_json.return_value = "baz"
        mocked_key_calculation.return_value = "bar"
        self.publisher.redis_client.setnx = Mock("redis_client_setter")
        self.publisher.redis_client.setnx.return_value = True
        self.publisher.redis_client.publish = Mock("redis_client_publish")
        self.publisher.redis_client.publish.return_value = 1

        self.publisher.publish()

        mocked_get_player_news.assert_called_once()
        mocked_to_json.assert_called_once_with(player_news_item="foo")
        mocked_key_calculation.assert_called_once_with(player_news_item="foo")
        self.publisher.redis_client.setnx.assert_called_once_with(name="bar", value="baz")
        self.publisher.redis_client.publish.assert_called_once_with(channel=REDIS_PLAYER_NEWS_CHANNEL_NAME,
                                                                    message="baz")




