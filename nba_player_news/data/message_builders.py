# -*- coding: utf-8 -*-
from __future__ import division

import datetime
import logging
import logging.config
from nltk import tokenize
import math
import pytz

from nba_player_news.data.messages import SubscriptionMessage
from nba_player_news.models import Subscription


class EmailMessageBuilder:

    message_body_format = """
        <h3>{headline}</h3>
        <h4>{caption}</h4>
        <div>{description}</div>
        {injury_details_body}
        <h5>Published At: {published_at}</h5>
    """
    injury_details_body_format = """
        <h5>Injury Details</h5>
        <div>Status: {status} | {side} {affected_area} {detail}<div>
    """

    def __init__(self, message):
        self.message = message

    def build(self):
        injury_details_body = ""
        if self.message["injury"]["is_injured"]:
            injury_details_body = self.build_injury_details_body()

        return EmailMessageBuilder.message_body_format.format(
            headline=self.message["headline"],
            caption=self.message["caption"],
            description=self.message["description"],
            injury_details_body=injury_details_body,
            first_name=self.message["first_name"],
            last_name=self.message["last_name"],
            position=self.message["position"],
            team=self.message["team"],
            published_at=datetime.datetime.fromtimestamp(timestamp=self.message["published_at_unix_timestamp"]).isoformat()
        )

    def build_injury_details_body(self):
        return EmailMessageBuilder.injury_details_body_format.format(
            status=self.message["injury"]["status"],
            affected_area=self.message["injury"]["affected_area"],
            side=self.message["injury"]["side"],
            detail=self.message["injury"]["detail"]
        )


class TwitterMessageBuilder:

    message_format = """
    {headline}

    {caption}

    {description}

    {injury_details}

    Published At: {published_at}
    """

    injury_details_format = """
    Status: {status} | {side} {affected_area} {detail}
    """

    def __init__(self, message):
        self.message = message

    def build(self):
        return TwitterMessageBuilder.message_format.format(
            headline=self.message["headline"],
            caption=self.message["caption"],
            description=self.message["description"],
            injury_details=self.build_injury_details(),
            published_at=datetime.datetime.fromtimestamp(timestamp=self.message["published_at_unix_timestamp"]).isoformat()
        )

    def build_injury_details(self):
        if not self.message["injury"]["is_injured"]:
            return ""

        return TwitterMessageBuilder.injury_details_format.format(
            status=self.message["injury"]["status"],
            affected_area=self.message["injury"]["affected_area"],
            side=self.message["injury"]["side"],
            detail=self.message["injury"]["detail"]
        )


class FacebookMessengerMessageBuilder:

    max_message_length = 640
    message_format = """
    {headline}

    {caption}

    {description}

    {injury_details}

    Published At: {published_at}
    """

    injury_details_format = """
    Status: {status} | {side} {affected_area} {detail}
    """

    def __init__(self, message):
        self.message = message

    def build_with_index(self, index, total_messages, text):
        return """
        {headline}

        {text}
        """.format(headline="{} ({}/{})".format(self.message["headline"], index, total_messages),
                   text=text)

    def build(self):
        return FacebookMessengerMessageBuilder.message_format.format(
            headline=self.message["headline"],
            caption=self.message["caption"],
            description=self.message["description"],
            injury_details=self.build_injury_details(),
            published_at=datetime.datetime.fromtimestamp(timestamp=self.message["published_at_unix_timestamp"]).isoformat()
        )

    def build_injury_details(self):
        if not self.message["injury"]["is_injured"]:
            return ""

        return FacebookMessengerMessageBuilder.injury_details_format.format(
            status=self.message["injury"]["status"],
            affected_area=self.message["injury"]["affected_area"],
            side=self.message["injury"]["side"],
            detail=self.message["injury"]["detail"]
        )

    def headline(self, index, total_messages):
        return """
        {value} ({index}/{total_messages})
        """.format(value=self.message["headline"], index=index, total_messages=total_messages)

    def description_sentences(self):
        return tokenize.sent_tokenize(self.message["description"])

    def caption(self):
        return """
{caption}

""".format(caption=self.message["caption"])

    def footer(self):
        published_at = datetime.datetime.fromtimestamp(timestamp=self.message["published_at_unix_timestamp"])
        published_at = published_at.replace(tzinfo=pytz.utc)
        published_at = published_at.astimezone(pytz.timezone("America/New_York"))

        return """{injury_details}

Published At: {published_at} EST
        """.format(injury_details=self.build_injury_details(),
                   published_at=published_at.strftime("%Y-%m-%d %-I:%M %p"))

    def build_messages(self):
        message = self.build()
        if len(message) > FacebookMessengerMessageBuilder.max_message_length:
            messages = []
            message_length = FacebookMessengerMessageBuilder.max_message_length
            message_count = int(math.ceil(len(message) / message_length))
            footer = self.footer()
            # add for safety
            if len(message) > message_count * message_length + len(footer):
                message_count += 1
            sentence_index = 0
            sentences = self.description_sentences()
            for index in range(0, message_count):
                current_message = self.headline(index=index + 1, total_messages=message_count)
                if index == 0:
                    current_message += self.caption()
                message_sentences = []
                for message_sentence_index in range(sentence_index, len(sentences)):
                    sentence = sentences[message_sentence_index]
                    if len(current_message + sentence + footer) > message_length:
                        break
                    else:
                        message_sentences.append(sentence)
                        sentence_index += 1
                current_message += " ".join(message_sentences)
                if index == message_count - 1:
                    current_message += footer
                messages.append(current_message.strip())
            return messages
        else:
            return [message]


class FacebookSubscriberMessageBuilder:
    def __init__(self, event_data):
        self.event_data = event_data
        self.user_id = self.event_data["entry"][0]["messaging"][0]["sender"]["id"]

    def build(self):
        logging.info("Event data: {}".format(self.event_data))
        message_event = self.event_data["entry"][0]["messaging"][0]
        sender_id = message_event["sender"]["id"]
        message_text = message_event["message"]["text"]
        if message_text.lower() == "subscribe":
            return self.build_subscribe_message()
        elif message_text.lower() == "unsubscribe":
            return self.build_unsubscribe_message()
        else:
            return SubscriptionMessage(platform="facebook", platform_identifier=sender_id,
                                       text="Type 'Subscribe' or 'Unsubscribe'")

    def build_subscribe_message(self):
        subscription, created = Subscription.objects.get_or_create(platform="facebook",
                                                                   platform_identifier=self.user_id)
        logging.info("Subscription: {} was created: {} for user: {}".format(subscription, created, self.user_id))

        if created:
            return SubscriptionMessage(platform="facebook", platform_identifier=self.user_id,
                                       text="You are now subscribed!")

        elif subscription.unsubscribed_at is not None:
            subscription.update(unsubscribed_at=None)
            logging.info("User: {} was resubscribed".format(self.user_id))
            return SubscriptionMessage(platform="facebook", platform_identifier=self.user_id,
                                       text="Thanks for resubscribing!")

        else:
            logging.info("User: {} is already subscribed".format(self.user_id))
            return SubscriptionMessage(platform="facebook", platform_identifier=self.user_id,
                                       text="You are already subscribed!")

    def build_unsubscribe_message(self):
        if not Subscription.objects.filter(platform="facebook", platform_identifier=self.user_id).exists():
            logging.info("User: {} is not subscribed".format(self.user_id))
            return SubscriptionMessage(platform="facebook", platform_identifier=self.user_id,
                                       text="You don't have a subscription!")
        else:
            logging.info("User: {} is already unsubscribed".format(self.user_id))
            Subscription.objects.filter(platform="facebook", platform_identifier=self.user_id).first()\
                                .update(unsubscribed_at=datetime.datetime.now())
            return SubscriptionMessage(platform="facebook", platform_identifier=self.user_id,
                                       text="You were unsubscribed!")