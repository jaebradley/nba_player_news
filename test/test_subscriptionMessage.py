import json
from unittest import TestCase

from nba_player_news.data.messages import SubscriptionMessage


class TestSubscriptionMessage(TestCase):
    platform = "foo"
    platform_identifier = "bar"
    text = "baz"
    message = SubscriptionMessage(platform=platform, platform_identifier=platform_identifier, text=text)

    def test_instantiation(self):
        self.assertEqual(self.message.platform, self.platform)
        self.assertEqual(self.message.platform_identifier, self.platform_identifier)
        self.assertEqual(self.message.text, self.text)

    def test_to_json(self):
        expected = json.dumps({
            "platform": self.platform,
            "platform_identifier": self.platform_identifier,
            "text": self.text
        })
        self.assertEqual(self.message.to_json(), expected)

    def test_unicode(self):
        expected = "Platform: foo | Platform Identifier: bar | Text: baz"
        self.assertEqual(self.message.__unicode__(), expected, "")

    def test_not_equal(self):
        another_message = SubscriptionMessage(platform="jae", platform_identifier="baebae", text="jaebaebae")
        self.assertNotEqual(self.message, another_message)

    def test_equal(self):
        self.assertEqual(self.message, self.message)

    def test_hash(self):
        self.assertEqual(self.message.__hash__(),  hash(tuple(sorted(self.message.__dict__.items()))))
