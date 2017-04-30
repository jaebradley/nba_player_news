from django.core.management.base import BaseCommand

from nba_player_news.data.subscriber import Subscriber


class Command(BaseCommand):
    def __init__(self, stdout=None, stderr=None, no_color=False):
        super(Command, self).__init__(stdout, stderr, no_color)

    def handle(self, *args, **options):
        Command.process_messages()

    @staticmethod
    def process_messages():
        Subscriber().process_messages()