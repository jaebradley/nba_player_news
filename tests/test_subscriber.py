from unittest import TestCase

from nba_player_news.data.subscriber_event.outcomes import SubscriberEventOutcome
from nba_player_news.data.subscriber_event.processors import Subscriber


class MockSubscription:
    def __init__(self, unsubscribed_at):
        self.unsubscribed_at = unsubscribed_at


class MockSubscriptions:
    def __init__(self):
        pass

    def get_or_create(self, platform, platform_identifier):
        if platform == "jae":
            return MockSubscription(unsubscribed_at=None), True

        if platform_identifier == "jae":
            return MockSubscription(unsubscribed_at="baebae"), False

        return MockSubscription(unsubscribed_at=None), False


class TestSubscriber(TestCase):

    def test_instantiation(self):
        subscriptions = "jae"
        platform_name = "baebae"
        subscriber = Subscriber(subscriptions=subscriptions, platform_name=platform_name)
        self.assertEqual(subscriber.subscriptions, subscriptions)
        self.assertEqual(subscriber.platform_name, platform_name)

    def test_subscription_creation(self):
        subscriptions = MockSubscriptions()
        subscriber = Subscriber(subscriptions=subscriptions, platform_name="jae")
        self.assertEqual(subscriber.process(user_id="foo"), SubscriberEventOutcome.subscription_created)

    def test_resubscription(self):
        subscriptions = MockSubscriptions()
        subscriber = Subscriber(subscriptions=subscriptions, platform_name="foo")
        self.assertEqual(subscriber.process(user_id="jae"), SubscriberEventOutcome.resubscribed)

    def test_already_subscribed(self):
        subscriptions = MockSubscriptions()
        subscriber = Subscriber(subscriptions=subscriptions, platform_name="foo")
        self.assertEqual(subscriber.process(user_id="bar"), SubscriberEventOutcome.already_subscribed)
