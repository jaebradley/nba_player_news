import json
from unittest import TestCase

import mock

import environment
from nba_player_news.data.senders import FacebookMessager


def mock_post_request(**kwargs):
    class MockResponse:
        def __init__(self):
            self.status_code = "jae"

        def json(self):
            return "baebae"

    return MockResponse()


class TestFacebookMessager(TestCase):

    def test_data_building(self):
        recipient_id = 1
        message = "jaebaebae"
        expected = json.dumps({
            "recipient": {
                "id": recipient_id
            },
            "message": {
                "text": message
            }
        })
        self.assertEqual(FacebookMessager.build_data(recipient_id=recipient_id, message=message), expected)

    def test_instantiation(self):
        messager = FacebookMessager()
        self.assertEqual(messager.base_url, "https://graph.facebook.com/v2.6/me/messages")
        self.assertEqual(messager.base_parameters, {"access_token": environment.FACEBOOK_PAGE_ACCESS_TOKEN})
        self.assertEqual(messager.headers, {"Content-Type": "application/json"})

    @mock.patch("requests.post", side_effect=mock_post_request)
    def test_send(self, mocked_post):
        recipient_id = 1
        message = "jaebaebae"
        messager = FacebookMessager()
        result = messager.send(recipient_id=recipient_id, message=message)
        request_args, request_kwargs = mocked_post.call_args
        expected_data = FacebookMessager.build_data(recipient_id=recipient_id, message=message)
        self.assertEqual(messager.base_url, request_kwargs["url"])
        self.assertEqual(messager.base_parameters, request_kwargs["params"])
        self.assertEqual(messager.headers, request_kwargs["headers"])
        self.assertEqual(messager.headers, request_kwargs["headers"])
        self.assertEqual(expected_data, request_kwargs["data"])
        self.assertEqual(result.status_code, "jae")
        self.assertEqual(result.json(), "baebae")
