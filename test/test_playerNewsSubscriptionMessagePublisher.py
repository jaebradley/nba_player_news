from unittest import TestCase

from mock import Mock

from environment import REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME
from nba_player_news.data.messages import SubscriptionMessage
from nba_player_news.data.publishers import PlayerNewsSubscriptionMessagePublisher


class MockSubscription:

    def __init__(self, platform, platform_identifier):
        self.platform = platform
        self.platform_identifier = platform_identifier


class TestPlayerNewsSubscriptionMessagePublisher(TestCase):

    def test_publishing_subscription_message(self):
        expected_subscriber_count = 1
        publisher = PlayerNewsSubscriptionMessagePublisher()
        publisher.redis_client.publish = Mock("redis_client_publish")
        publisher.redis_client.publish.returns = expected_subscriber_count

        expected_platform = "platform"
        expected_platform_identifier = "platform identifier"
        subscription = MockSubscription(platform=expected_platform, platform_identifier=expected_platform_identifier)

        expected_message = "message"

        publisher.publish(subscription=subscription, message=expected_message)

        expected_subscription_message = SubscriptionMessage(platform=expected_platform,
                                                            platform_identifier=expected_platform_identifier,
                                                            text=expected_message)

        publisher.redis_client.publish.assert_called_once_with(channel=REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME,
                                                               message=expected_subscription_message.to_json())
