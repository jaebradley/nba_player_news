from django.core.management.base import BaseCommand

from nba_player_news.data.subscribers import PlayerNewsSubscriber
from nba_player_news.data.subscribers import SubscriberEventsSubscriber
from nba_player_news.data.subscribers import SubscriptionMessagesSubscriber


class Command(BaseCommand):
    def __init__(self, stdout=None, stderr=None, no_color=False):
        super(Command, self).__init__(stdout, stderr, no_color)

    def handle(self, *args, **options):
        Command.process_messages()

    @staticmethod
    def process_messages():
        PlayerNewsSubscriber().process_messages()
        SubscriberEventsSubscriber().process_messages()
        SubscriptionMessagesSubscriber().process_messages()
