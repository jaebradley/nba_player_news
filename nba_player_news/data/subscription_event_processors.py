import os
import logging
import logging.config
import datetime

from nba_player_news.models import Subscription
from nba_player_news.data.senders import FacebookMessager

logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "../../logger.conf"))
logger = logging.getLogger("subscriptionEvents")


class FacebookSubscriptionEventsProcessor:
    def __init__(self):
        self.messager = FacebookMessager()

    def process(self, event_data):
        if event_data.get("object") == "page":
            for entry in event_data.get("entry"):
                for message_event in entry["messaging"]:
                    if "message" in message_event:
                        sender_id = message_event["sender"]["id"]
                        recipient_id = message_event["recipient"]["id"]
                        message_text = message_event["message"]["text"]
                        logger.info("Sender: {} | Recipient: {} | Message: {}".format(sender_id, recipient_id, message_text))
                        if message_text.lower() == "subscribe":
                            self.process_subscribe_event(user_id=sender_id)
                        elif message_text.lower() == "unsubscribe":
                            self.process_unsubscribe_event(user_id=sender_id)

    def process_subscribe_event(self, user_id):
        subscription, created = Subscription.objects.get_or_create(platform="facebook", platform_identifier=user_id)
        if created:
            self.messager.send(recipient_id=user_id, message="You are now subscribed!")

        elif subscription.unsubscribed_at is not None:
            subscription.unsubscribed_at = None
            subscription.save()
            self.messager.send(recipient_id=user_id, message="Thanks for resubscribing!")

    def process_unsubscribe_event(self, user_id):
        if not Subscription.objects.filter(platform="facebook", platform_identifier=user_id).exists():
            self.messager.send(recipient_id=user_id, message="You don't have a subscription!")
        else:
            Subscription.objects.filter(platform="facebook", platform_identifier=user_id).first().update(unsubscribed_at=datetime.datetime.now())
            self.messager.send(recipient_id=user_id, message="You were unsubscribed!")

