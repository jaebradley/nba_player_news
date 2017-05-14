from unittest import TestCase
from mock import Mock

from nba_player_news.data.subscriber_event.processors import FacebookSubscriberEventProcessor
from nba_player_news.data.subscriber_event.outcomes import SubscriberEventOutcome
from nba_player_news.data.messages import SubscriptionMessage
from environment import REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME


class MockSubscriptionMessage:
    def __init__(self, value):
        self.value = value

    def to_json(self):
        return self.value


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

    def test_subscriber_event_message_text(self):
        expected_text = "jaebaebae"
        subscriber_event_message = {
            "entry": [
                {
                    "messaging": [
                        {
                            "message": {
                                "text": expected_text
                            }
                        }
                    ]
                }
            ]
        }
        processor = FacebookSubscriberEventProcessor()
        message_text = processor.subscriber_event_message_text(subscriber_event_message=subscriber_event_message)
        self.assertEqual(message_text, expected_text)

    def test_subscriber_id(self):
        expected_id = "jaebaebae"
        subscriber_event_message = {
            "entry": [
                {
                    "messaging": [
                        {
                            "sender": {
                                "id": expected_id
                            }
                        }
                    ]
                }
            ]
        }
        processor = FacebookSubscriberEventProcessor()
        subscriber_id = processor.subscriber_id(subscriber_event_message=subscriber_event_message)
        self.assertEqual(subscriber_id, expected_id)

    def test_is_unsubscriber(self):
        processor = FacebookSubscriberEventProcessor()
        self.assertTrue(processor.is_unsubscriber(subscriber_event_message_text="UNSUBSCRIBE"))

    def test_is_not_unsubscriber(self):
        processor = FacebookSubscriberEventProcessor()
        self.assertFalse(processor.is_unsubscriber(subscriber_event_message_text="SUBSCRIBE"))

    def test_is_subscriber(self):
        processor = FacebookSubscriberEventProcessor()
        self.assertTrue(processor.is_subscriber(subscriber_event_message_text="SUBSCRIBE"))

    def test_is_not_subscriber(self):
        processor = FacebookSubscriberEventProcessor()
        self.assertFalse(processor.is_subscriber(subscriber_event_message_text="UNSUBSCRIBE"))

    def test_subscription_message_for_subscriber(self):
        subscriber_id = "jae"
        subscriber_event_message_text = "baebae"
        subscription_message_text = "foobar"
        processor = FacebookSubscriberEventProcessor()
        processor.subscriber.process = Mock("subscriber_processing")
        processor.subscriber.process.return_value = "foo"

        processor.subscription_message_text = Mock("subscription_message_text")
        processor.subscription_message_text.return_value = subscription_message_text

        processor.is_subscriber = Mock("is_subscriber")
        processor.is_subscriber.return_value = True

        message = processor.subscription_message(subscriber_id=subscriber_id,
                                                 subscriber_event_message_text=subscriber_event_message_text)
        expected = SubscriptionMessage(platform=processor.platform, platform_identifier=subscriber_id,
                                       text=subscription_message_text)

        self.assertEqual(message, expected)
        processor.subscriber.process.assert_called_once_with(user_id=subscriber_id)

    def test_subscription_message_for_unsubscriber(self):
        subscriber_id = "jae"
        subscriber_event_message_text = "baebae"
        subscription_message_text = "foobar"
        processor = FacebookSubscriberEventProcessor()
        processor.subscriber.process = Mock("subscriber_processing")
        processor.subscriber.process.return_value = "foo"

        processor.subscription_message_text = Mock("subscription_message_text")
        processor.subscription_message_text.return_value = subscription_message_text

        processor.is_subscriber = Mock("is_subscriber")
        processor.is_subscriber.return_value = False

        processor.is_unsubscriber = Mock("is_unsubscriber")
        processor.is_unsubscriber.return_value = True

        message = processor.subscription_message(subscriber_id=subscriber_id,
                                                 subscriber_event_message_text=subscriber_event_message_text)
        expected = SubscriptionMessage(platform=processor.platform, platform_identifier=subscriber_id,
                                       text=subscription_message_text)

        self.assertEqual(message, expected)

    def test_subscription_message_for_neither_subscriber_nor_unsubscriber(self):
        subscriber_id = "jae"
        subscriber_event_message_text = "baebae"
        subscription_message_text = "Type 'Subscribe' or 'Unsubscribe'."
        processor = FacebookSubscriberEventProcessor()
        processor.subscriber.process = Mock("subscriber_processing")
        processor.subscriber.process.return_value = "foo"

        processor.subscription_message_text = Mock("subscription_message_text")
        processor.subscription_message_text.return_value = subscription_message_text

        processor.is_subscriber = Mock("is_subscriber")
        processor.is_subscriber.return_value = False

        processor.is_unsubscriber = Mock("is_unsubscriber")
        processor.is_unsubscriber.return_value = False

        message = processor.subscription_message(subscriber_id=subscriber_id,
                                                 subscriber_event_message_text=subscriber_event_message_text)
        expected = SubscriptionMessage(platform=processor.platform, platform_identifier=subscriber_id,
                                       text=subscription_message_text)

        self.assertEqual(message, expected)

    def test_process(self):
        subscriber_event_message = "subscriber event message"
        expected_subscriber_id = "jae"
        expected_subscriber_event_message_text = "baebae"
        expected_subscription_message = MockSubscriptionMessage("foobar")
        expected_subscriber_count = "baz"
        processor = FacebookSubscriberEventProcessor()

        processor.subscriber_id = Mock("subscriber_id")
        processor.subscriber_id.return_value = expected_subscriber_id

        processor.subscriber_event_message_text = Mock("subscriber_event_message_text")
        processor.subscriber_event_message_text.return_value = expected_subscriber_event_message_text

        processor.subscription_message = Mock("subscription_message")
        processor.subscription_message.return_value = expected_subscription_message

        processor.redis_client.publish = Mock("redis_client_publish")
        processor.redis_client.publish.return_value = expected_subscriber_count

        processor.process(subscriber_event_message)

        processor.subscriber_id.assert_called_once_with(subscriber_event_message)
        processor.subscriber_event_message_text.assert_called_once_with(subscriber_event_message)
        processor.subscription_message.assert_called_once_with(subscriber_id=expected_subscriber_id,
                                                               subscriber_event_message_text=expected_subscriber_event_message_text)
        processor.redis_client.publish.assert_called_once_with(channel=REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME,
                                                               message=expected_subscription_message.to_json())
