import datetime
import logging
import logging.config
import redis

from nba_player_news.models import Subscription
from outcomes import SubscriberEventOutcome
from nba_player_news.data.messages import SubscriptionMessage
from environment import REDIS_URL, REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME


class FacebookSubscriberEventProcessor:
    logger = logging.getLogger("publisher")
    subscriber_event_outcome_messages = {
        SubscriberEventOutcome.subscription_created: "You are now subscribed!",
        SubscriberEventOutcome.resubscribed: "Thanks for resubscribing!",
        SubscriberEventOutcome.already_subscribed: "You are already subscribed!",
        SubscriberEventOutcome.subscription_does_not_exist: "You don't have a subscription!",
        SubscriberEventOutcome.already_unsubscribed: "You are already unsubscribed!",
        SubscriberEventOutcome.unsubscribed: "You were unsubscribed!"
    }

    def __init__(self):
        self.platform = "facebook"
        self.redis_client = redis.StrictRedis().from_url(url=REDIS_URL)
        self.subscriber = Subscriber(subscriptions=Subscription.objects, platform_name=self.platform)
        self.unsubscriber = Unsubscriber(subscriptions=Subscription.objects, platform_name=self.platform)

    def process(self, subscriber_event_message):
        FacebookSubscriberEventProcessor.logger.info("Processing message: {}".format(subscriber_event_message))

        subscriber_id = self.subscriber_id(subscriber_event_message)
        subscriber_event_message_text = self.subscriber_event_message_text(subscriber_event_message)
        subscription_message = self.subscription_message(subscriber_id=subscriber_id,
                                                         subscriber_event_message_text=subscriber_event_message_text)
        subscriber_count = self.redis_client.publish(channel=REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME,
                                                     message=subscription_message.to_json())

        FacebookSubscriberEventProcessor.logger.info(
            "Published message: {subscription_message} to {subscriber_count} subscribers on channel: {channel_name}"
            .format(subscription_message=subscription_message.to_json(), subscriber_count=subscriber_count,
                    channel_name=REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME)
        )

    def subscription_message(self, subscriber_id, subscriber_event_message_text):
        if self.is_subscriber(subscriber_event_message_text):
            outcome = self.subscriber.process(user_id=subscriber_id)
            return SubscriptionMessage(platform=self.platform, platform_identifier=subscriber_id,
                                       text=self.subscription_message_text(subscriber_event_outcome=outcome))

        elif self.is_unsubscriber(subscriber_event_message_text):
            outcome = self.unsubscriber.process(user_id=subscriber_id)
            return SubscriptionMessage(platform=self.platform, platform_identifier=subscriber_id,
                                       text=self.subscription_message_text(subscriber_event_outcome=outcome))
        else:
            return SubscriptionMessage(platform=self.platform, platform_identifier=subscriber_id,
                                       text="Type 'Subscribe' or 'Unsubscribe'.")

    def is_subscriber(self, subscriber_event_message_text):
        return subscriber_event_message_text.lower() == "subscribe"

    def is_unsubscriber(self, subscriber_event_message_text):
        return subscriber_event_message_text.lower() == "unsubscribe"

    def subscriber_event_message_text(self, subscriber_event_message):
        return subscriber_event_message["entry"][0]["messaging"][0]["message"]["text"]

    def subscriber_id(self, subscriber_event_message):
        return subscriber_event_message["entry"][0]["messaging"][0]["sender"]["id"]

    def subscription_message_text(self, subscriber_event_outcome):
        outcome_message = FacebookSubscriberEventProcessor.subscriber_event_outcome_messages.get(subscriber_event_outcome)

        if outcome_message is None:
            raise KeyError("Unknown outcome: {outcome}".format(outcome=subscriber_event_outcome))

        return outcome_message


class Subscriber:
    def __init__(self, subscriptions, platform_name):
        self.subscriptions = subscriptions
        self.platform_name = platform_name

    def process(self, user_id):
        subscription, created = self.subscriptions.get_or_create(platform=self.platform_name,
                                                                 platform_identifier=user_id)

        if created:
            return SubscriberEventOutcome.subscription_created

        if subscription.unsubscribed_at is not None:
            return SubscriberEventOutcome.resubscribed

        return SubscriberEventOutcome.already_subscribed


class Unsubscriber:
    def __init__(self, subscriptions, platform_name):
        self.subscriptions = subscriptions
        self.platform_name = platform_name

    def process(self, user_id):
        if not self.subscription_exists(user_id=user_id):
            return SubscriberEventOutcome.subscription_does_not_exist

        if self.unsubscribed(user_id=user_id):
            return SubscriberEventOutcome.already_unsubscribed

        self.unsubscribe(user_id=user_id)

        return SubscriberEventOutcome.unsubscribed

    def subscription_exists(self, user_id):
        return self.subscriptions.filter(platform=self.platform_name, platform_identifier=user_id).exists()

    def unsubscribed(self, user_id):
        return self.subscriptions.get(platform=self.platform_name, platform_identifier=user_id)\
                   .unsubscribed_at is not None

    def unsubscribe(self, user_id):
        subscription = self.subscriptions.get(platform=self.platform_name, platform_identifier=user_id)
        subscription.unsubscribed_at = datetime.datetime.now()
        subscription.save()
