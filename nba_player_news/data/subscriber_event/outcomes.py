from enum import Enum


class SubscriberEventOutcome(Enum):
    subscription_created = "subscription created"
    resubscribed = "resubscribed"
    already_subscribed = "already subscribed"
    unsubscribed = "unsubscribed"
    already_unsubscribed = "already unsubscribed"
    subscription_does_not_exist = "subscription does not exist"