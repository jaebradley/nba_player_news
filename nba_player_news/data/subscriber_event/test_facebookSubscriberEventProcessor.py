from unittest import TestCase

from nba_player_news.data.subscriber_event.processors import FacebookSubscriberEventProcessor
from nba_player_news.data.subscriber_event.outcomes import SubscriberEventOutcome


class TestFacebookSubscriberEventProcessor(TestCase):

    def test_you_are_now_subscribed_message_text(self):
        processor = FacebookSubscriberEventProcessor()
        message_text = processor.subscription_message_text(subscriber_event_outcome=SubscriberEventOutcome.subscription_created)
        self.assertEqual(message_text, "You are now subscribed!")

    def test_resubscribed_message_text(self):
        processor = FacebookSubscriberEventProcessor()
        message_text = processor.subscription_message_text(subscriber_event_outcome=SubscriberEventOutcome.resubscribed)
        self.assertEqual(message_text, "Thanks for resubscribing!")

    def test_already_subscribed_message_text(self):
        processor = FacebookSubscriberEventProcessor()
        message_text = processor.subscription_message_text(subscriber_event_outcome=SubscriberEventOutcome.already_subscribed)
        self.assertEqual(message_text, "You are already subscribed!")

    def test_subscription_does_not_exist_message_text(self):
        processor = FacebookSubscriberEventProcessor()
        message_text = processor.subscription_message_text(subscriber_event_outcome=SubscriberEventOutcome.subscription_does_not_exist)
        self.assertEqual(message_text, "You don't have a subscription!")

    def test_subscription_already_unsubscribed_message_text(self):
        processor = FacebookSubscriberEventProcessor()
        message_text = processor.subscription_message_text(subscriber_event_outcome=SubscriberEventOutcome.already_unsubscribed)
        self.assertEqual(message_text, "You are already unsubscribed!")

    def test_unsubscribed_message_text(self):
        processor = FacebookSubscriberEventProcessor()
        message_text = processor.subscription_message_text(subscriber_event_outcome=SubscriberEventOutcome.unsubscribed)
        self.assertEqual(message_text, "You were unsubscribed!")
