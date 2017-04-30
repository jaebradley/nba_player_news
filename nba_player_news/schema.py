from graphene import ObjectType as GrapheneObjectType, Schema, Node, NonNull, Int
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from nba_player_news.models import SubscriptionPlatform as SubscriptionPlatformModel, Subscription as SubscriptionModel


class SubscriptionPlatform(DjangoObjectType):
    class Meta:
        model = SubscriptionPlatformModel
        interfaces = (Node,)
        filter_fields = {
            "name": ["iexact", "icontains", "istartswith"]
        }


class Subscription(DjangoObjectType):
    class Meta:
        model = SubscriptionModel
        interfaces = (Node,)
        filter_fields = {
            "platform": ["iexact", "icontains", "istartswith"],
            "identifier": ["iexact", "icontains", "istartswith"]
        }


class Query(GrapheneObjectType):
    subscription_platform = Node.field(SubscriptionPlatform)
    subscription_platforms = DjangoFilterConnectionField(SubscriptionPlatform, first=NonNull(Int))

    subscription = Node.field(Subscription)
    subscriptions = DjangoFilterConnectionField(Subscription, first=NonNull(Int))

schema = Schema(query=Query)
