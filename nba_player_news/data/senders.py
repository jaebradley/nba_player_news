import yagmail
import os
import logging
import logging.config


from environment import GMAIL_PASSWORD, GMAIL_USERNAME
from nba_player_news.data.sent_message_builders import EmailMessageBuilder


class Emailer:
    logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "../../logger.conf"))
    logger = logging.getLogger("emailer")

    def __init__(self):
        self.client = yagmail.SMTP(user=GMAIL_USERNAME, password=GMAIL_PASSWORD)

    def send(self, destination, message):
        Emailer.logger.info("Sending message on behalf of user: {} to {} with message: {}".format(GMAIL_USERNAME, destination, message))
        self.client.send(
            to=destination,
            subject=message.headline,
            contents=EmailMessageBuilder(message=message).build()
        )

