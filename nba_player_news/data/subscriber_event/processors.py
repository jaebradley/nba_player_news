import datetime

from outcomes import SubscriberEventOutcome


class Subscriber:
    def __init__(self, subscription_model, platform_name):
        self.subscription_model = subscription_model
        self.platform_name = platform_name

    def process(self, user_id):
        subscription, created = self.get_or_create_subscription(user_id=user_id)

        if created:
            return SubscriberEventOutcome.subscription_created

        if subscription.unsubscribed_at is not None:
            return SubscriberEventOutcome.resubscribed

        return SubscriberEventOutcome.already_subscribed

    def get_or_create_subscription(self, user_id):
        return self.subscription_model.objects.get_or_create(platform=self.platform_name,
                                                             platform_identifier=user_id)


class Unsubscriber:
    def __init__(self, subscription_model, platform_name):
        self.subscription_model = subscription_model
        self.platform_name = platform_name

    def process(self, user_id):
        if not self.subscription_exists(user_id=user_id):
            return SubscriberEventOutcome.subscription_does_not_exist

        else:
            if self.unsubscribed(user_id=user_id):
                return SubscriberEventOutcome.already_unsubscribed

            self.unsubscribe(user_id=user_id)

            return SubscriberEventOutcome.unsubscribed

    def subscription_exists(self, user_id):
        return self.subscription_model.objects\
                                      .filter(platform=self.platform_name, platform_identifier=user_id)\
                                      .exists()

    def get_subscription(self, user_id):
        return self.subscription_model.objects.get(platform=self.platform_name, platform_identifier=user_id)

    def unsubscribed(self, user_id):
        return self.get_subscription(user_id=user_id).unsubscribed_at is not None

    def unsubscribe(self, user_id):
        self.get_subscription(user_id=user_id).update(unsubscribed_at=datetime.datetime.now())
