import datetime
import logging
import logging.config

from nba_player_news.data.messages import SubscriptionMessage
from nba_player_news.models import Subscription

logger = logging.getLogger("subscriptionEvents")


class FacebookSubscriberMessageBuilder:
    def __init__(self):
        pass

    def process(self, event_data):
        logging.info("Event data: {}".format(event_data))
        message_event = event_data["entry"][0]["messaging"][0]
        sender_id = message_event["sender"]["id"]
        message_text = message_event["message"]["text"]
        if message_text.lower() == "subscribe":
            return self.process_subscribe_event(user_id=sender_id)
        elif message_text.lower() == "unsubscribe":
            return self.process_unsubscribe_event(user_id=sender_id)
        else:
            return SubscriptionMessage(platform="facebook", platform_identifier=sender_id,
                                       text="Type 'Subscribe' or 'Unsubscribe'")

    def process_subscribe_event(self, user_id):
        subscription, created = Subscription.objects.get_or_create(platform="facebook", platform_identifier=user_id)
        logging.info("Subscription: {} was created: {} for user: {}".format(subscription, created, user_id))

        if created:
            return SubscriptionMessage(platform="facebook", platform_identifier=user_id,
                                       text="You are now subscribed!")

        elif subscription.unsubscribed_at is not None:
            subscription.update(unsubscribed_at=None)
            logging.info("User: {} was resubscribed".format(user_id))
            return SubscriptionMessage(platform="facebook", platform_identifier=user_id,
                                       text="Thanks for resubscribing!")

        else:
            logging.info("User: {} is already subscribed".format(user_id))
            return SubscriptionMessage(platform="facebook", platform_identifier=user_id,
                                       text="You are already subscribed!")

    def process_unsubscribe_event(self, user_id):
        if not Subscription.objects.filter(platform="facebook", platform_identifier=user_id).exists():
            logging.info("User: {} is not subscribed".format(user_id))
            return SubscriptionMessage(platform="facebook", platform_identifier=user_id,
                                       text="You don't have a subscription!")
        else:
            logging.info("User: {} is already unsubscribed".format(user_id))
            Subscription.objects.filter(platform="facebook", platform_identifier=user_id).first()\
                                .update(unsubscribed_at=datetime.datetime.now())
            return SubscriptionMessage(platform="facebook", platform_identifier=user_id,
                                       text="You were unsubscribed!")

