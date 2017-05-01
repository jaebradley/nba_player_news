import os
import logging
import logging.config

from nba_player_news.models import Subscription
from nba_player_news.data.senders import Emailer


class EmailSubscriptionsPublisher:
    logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "../../logger.conf"))
    logger = logging.getLogger("emailSubscriptionsPublisher")

    def __init__(self):
        self.emailer = Emailer()

    def publish(self, message):
        for subscription in Subscription.objects.filter(platform="email"):
            EmailSubscriptionsPublisher.logger.info("Publishing message: {} to subscription: {}".format(message, subscription))
            self.emailer.send(destination=subscription.platform_identifier, message=message)