from graphene import ObjectType as GrapheneObjectType, Schema, Node, NonNull, Int, String, Field, Boolean, Mutation
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.debug import DjangoDebug

from nba_player_news.models import Subscription as SubscriptionModel


class Subscription(DjangoObjectType):
    platform = String()
    platform_identifier = String()

    class Meta:
        model = SubscriptionModel
        interfaces = (Node,)
        filter_fields = {
            "platform_identifier": ["iexact", "icontains", "istartswith"]
        }


class CreateSubscription(Mutation):
    class Input:
        platform = String()
        platform_identifier = String()

    ok = Boolean()
    subscription = Field(lambda: Subscription)

    @staticmethod
    def mutate(root, args, context, info):
        subscription = SubscriptionModel.objects.create(platform=args.get("platform"),
                                                        platform_identifier=args.get("platform_identifier"))

        return CreateSubscription(subscription=subscription, ok=True)


class Mutations(GrapheneObjectType):
    create_subscription = CreateSubscription.Field()


class Query(GrapheneObjectType):
    subscription = Node.Field(Subscription)
    all_subscriptions = DjangoFilterConnectionField(Subscription, first=NonNull(Int))
    node = Node.Field()
    viewer = Field(lambda: Query)
    debug = Field(DjangoDebug, name='__debug')

schema = Schema(query=Query, mutation=Mutations)
