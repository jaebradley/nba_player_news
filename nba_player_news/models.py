from __future__ import unicode_literals

# Create your models here.


from django.db.models import Model, ForeignKey, CASCADE, CharField, DateTimeField

from enumfields import EnumField
from enumfields import Enum


class SubscriptionPlatformEnum(Enum):
    email = "email"
    twitter = "twitter"


class SubscriptionPlatform(Model):
    name = EnumField(SubscriptionPlatformEnum, max_length=1)


class Subscription(Model):
    platform = ForeignKey(SubscriptionPlatform, on_delete=CASCADE)
    identifier = CharField(max_length=255)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("platform", "identifier")

    def __unicode__(self):
        return "platform: {} | identifier: {} | created_at: {} | updated_at: {}".format(self.platform, self.identifier, self.created_at, self.updated_at)
