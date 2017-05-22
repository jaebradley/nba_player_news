from django.test import TestCase
from mock import Mock, patch

import datetime

from nba_player_news.models import Subscription

from nba_player_news.data.publishers import PlayerNewsSubscriptionsMessagesPublisher


def mock_subscription_builder(subscription, player_news):
    return "{platform} {platform_identifier}".format(platform=subscription.platform,
                                                     platform_identifier=subscription.platform_identifier)


class MockSubscription:
    def __init__(self, platform):
        self.platform = platform


class TestPlayerNewsSubscriptionsMessagesPublisherMessageBuilding(TestCase):
    publisher = PlayerNewsSubscriptionsMessagesPublisher()

    @patch("nba_player_news.data.message_builders.FacebookMessengerMessageBuilder.build_messages")
    def successful_message_building(self, mock_message_builder):
        expected_player_news = "player_news"
        subscription = MockSubscription(platform="facebook")
        expected_messages = "messages"
        mock_message_builder.return_value = expected_messages

        self.publisher.build_messages(subscription=subscription, player_news=expected_player_news)
        self.assertEqual(self.publisher.build_messages(subscription=subscription, player_news=expected_player_news),
                         expected_messages)

    def throws_when_unknown_platform_when_building_messages(self):
        subscription = MockSubscription(platform="jaebaebae")
        expected_player_news = "player_news"
        self.assertRaises(RuntimeError, self.publisher.build_messages(subscription=subscription,
                                                                      player_news=expected_player_news))


class TestPlayerNewsSubscriptionsMessagesPublisherPublishing(TestCase):
    publisher = PlayerNewsSubscriptionsMessagesPublisher()

    def setUp(self):
        self.subscription_1 = Subscription.objects.create(platform="jae", platform_identifier="baebae")
        self.subscription_2 = Subscription.objects.create(platform="to_be", platform_identifier="unsubscribed")
        self.subscription_3 = Subscription.objects.create(platform="was", platform_identifier="unsubscribed",
                                                          unsubscribed_at=datetime.datetime.now())

    def publishes(self):
        expected_player_news = "player news"
        self.publisher.build_messages = Mock(side_effect=mock_subscription_builder)
        self.publisher.subscription_message_publisher.publish = Mock("subscription_message_publisher")
        self.publisher.build_messages.assert_called_with(subscription=self.subscription_1,
                                                         player_news=expected_player_news)
        self.publisher.build_messages.assert_called_with(subscription=self.subscription_2,
                                                         player_news=expected_player_news)
        self.publisher.build_messages.assert_called_with(subscription=self.subscription_3,
                                                         player_news=expected_player_news)
        self.publisher.subscription_message_publisher.publish.assert_called_with(subscription=self.subscription_1,
                                                                                 message="jae baebae")
        self.publisher.subscription_message_publisher.publish.assert_called_with(subscription=self.subscription_2,
                                                                                 message="to_be unsubscribed")
        self.publisher.subscription_message_publisher.publish.assert_called_with(subscription=self.subscription_3,
                                                                                 message="was unsubscribed")

