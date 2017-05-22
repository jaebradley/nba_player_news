import datetime

from django.test import TestCase
from mock import Mock

from nba_player_news.data.subscriber_event.outcomes import SubscriberEventOutcome
from nba_player_news.data.subscriber_event.processors import Unsubscriber
from nba_player_news.models import Subscription


class TestUnsubscriber(TestCase):

    def setUp(self):
        Subscription.objects.create(platform="jae", platform_identifier="baebae")
        Subscription.objects.create(platform="to_be", platform_identifier="unsubscribed")
        Subscription.objects.create(platform="was", platform_identifier="unsubscribed", unsubscribed_at=datetime.datetime.now())

    def test_instantiation(self):
        subscriptions = "jae"
        platform_name = "baebae"
        unsubscriber = Unsubscriber(subscriptions=subscriptions, platform_name=platform_name)
        self.assertEqual(unsubscriber.subscriptions, subscriptions)
        self.assertEqual(unsubscriber.platform_name, platform_name)

    def test_when_subscription_exists(self):
        unsubscriber = Unsubscriber(subscriptions=Subscription.objects, platform_name="jae")
        self.assertTrue(unsubscriber.subscription_exists(user_id="baebae"))

    def test_unsubscribed(self):
        unsubscriber = Unsubscriber(subscriptions=Subscription.objects, platform_name="was")
        self.assertTrue(unsubscriber.unsubscribed(user_id="unsubscribed"))

    def test_unsubscribe(self):
        subscription_to_be_unsubscribed = Subscription.objects.get(platform="to_be", platform_identifier="unsubscribed")
        self.assertIsNone(subscription_to_be_unsubscribed.unsubscribed_at)

        unsubscriber = Unsubscriber(subscriptions=Subscription.objects, platform_name="to_be")
        unsubscriber.unsubscribe(user_id="unsubscribed")

        subscription_to_be_unsubscribed = Subscription.objects.get(platform="to_be", platform_identifier="unsubscribed")
        self.assertIsNotNone(subscription_to_be_unsubscribed.unsubscribed_at)

    def test_processing_when_subscription_does_not_exists(self):
        unsubscriber = Unsubscriber(subscriptions="foo", platform_name="bar")
        unsubscriber.subscription_exists = Mock(name="subscription_exists")
        unsubscriber.subscription_exists.return_value = False
        self.assertEqual(unsubscriber.process(user_id="jaebaebae"), SubscriberEventOutcome.subscription_does_not_exist)

    def test_processing_when_subscription_exists_and_already_unsubscribed(self):
        unsubscriber = Unsubscriber(subscriptions="foo", platform_name="bar")
        unsubscriber.subscription_exists = Mock(name="subscription_exists")
        unsubscriber.unsubscribed = Mock(name="unsubscribed")
        unsubscriber.subscription_exists.return_value = True
        unsubscriber.unsubscribed.return_value = True
        self.assertEqual(unsubscriber.process(user_id="jaebaebae"), SubscriberEventOutcome.already_unsubscribed)

    def test_processing_when_subscription_exists_and_not_unsubscribed(self):
        unsubscriber = Unsubscriber(subscriptions="foo", platform_name="bar")
        unsubscriber.subscription_exists = Mock(name="subscription_exists")
        unsubscriber.unsubscribed = Mock(name="unsubscribed")
        unsubscriber.unsubscribe = Mock(name="unsubscribe")
        unsubscriber.subscription_exists.return_value = True
        unsubscriber.unsubscribed.return_value = False
        self.assertEqual(unsubscriber.process(user_id="jaebaebae"), SubscriberEventOutcome.unsubscribed)
        unsubscriber.unsubscribe.assert_called_once_with(user_id="jaebaebae")

