import datetime

from outcomes import SubscriberEventOutcome


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
