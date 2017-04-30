from __future__ import unicode_literals

# Create your models here.


from django.db.models import Model, CharField, DateTimeField


class Subscription(Model):
    platform = CharField(max_length=50, choices=(
        ("email", "Email"),
        ("twitter", "Twitter"),
    ))
    platform_identifier = CharField(max_length=255)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("platform", "platform_identifier")

    def __unicode__(self):
        return "platform: {} | platform_identifier: {} | created_at: {} | updated_at: {}".format(self.platform, self.platform_identifier, self.created_at, self.updated_at)
