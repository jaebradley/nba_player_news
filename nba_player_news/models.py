from __future__ import unicode_literals

# Create your models here.


from django.db.models import Model, CharField, DateTimeField, ForeignKey, CASCADE, TextField, BooleanField


class Subscription(Model):
    platform = CharField(max_length=50, choices=(
        ("email", "Email"),
        ("facebook", "Facebook"),
    ))
    platform_identifier = CharField(max_length=255)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    unsubscribed_at = DateTimeField(null=True)

    class Meta:
        unique_together = ("platform", "platform_identifier")

    def __unicode__(self):
        return "platform: {} | platform_identifier: {} | created_at: {} | updated_at: {} | unsubscribed_at: {}"\
            .format(self.platform, self.platform_identifier, self.created_at, self.updated_at, self.unsubscribed_at)


class SubscriptionAttempt(Model):
    subscription = ForeignKey(to=Subscription, on_delete=CASCADE)
    attempted_at = DateTimeField(auto_now_add=True)
    message = TextField(max_length=2048)

    def __unicode__(self):
        return "Subscription: {subscription} | Attempted at: {attempted_at} | Message: {message}"\
            .format(subscription=self.subscription, attempted_at=self.attempted_at, message=self.message)


class SubscriptionAttemptResult(Model):
    subscription_attempt = ForeignKey(to=SubscriptionAttempt, on_delete=CASCADE)
    resolved_at = DateTimeField(auto_now_add=True)
    successful = BooleanField
    response = TextField(max_length=2048)

    def __unicode__(self):
        return "Subscription Attempt: {subscription_attempt} | Resolved At: {resolved_at} | Successful: {successful} | Response: {response}"\
            .format(subscription_attempt=self.subscription_attempt, resolved_at=self.resolved_at,
                    successful=self.successful, response=self.response)
