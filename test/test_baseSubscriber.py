from unittest import TestCase

from nba_player_news.data.subscribers import BaseSubscriber


class TestBaseSubscriber(TestCase):

    subscriber = BaseSubscriber(subscription_channel_name="foo")

    def expect_process_message_to_not_be_implemented(self):
        self.assertRaises(NotImplementedError, self.subscriber.process_message(message="bar"))


