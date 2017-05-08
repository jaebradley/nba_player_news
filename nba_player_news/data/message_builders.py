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

    headline_format = """
    {value} ({index}/{total_messages})
    """

    footer_format = """
    {injury_details}

    Published At: {published_at} EST
    """

    caption_format = """
    {caption}

    """

    def __init__(self, message):
        self.message = message

    def build(self):
        return FacebookMessengerMessageBuilder.message_format.format(
            headline=self.message["headline"],
            caption=self.message["caption"],
            description=self.message["description"],
            injury_details=self.injury_details(),
            published_at=self.published_at()).strip()

    def injury_details(self):
        if not self.message["injury"]["is_injured"]:
            return ""

        return FacebookMessengerMessageBuilder.injury_details_format.format(
            status=self.message["injury"]["status"],
            affected_area=self.message["injury"]["affected_area"],
            side=self.message["injury"]["side"],
            detail=self.message["injury"]["detail"]
        )

    def headline(self, index, total_messages):
        return FacebookMessengerMessageBuilder.headline_format.format(value=self.message["headline"], index=index,
                                                                      total_messages=total_messages)

    def description_sentences(self):
        return tokenize.sent_tokenize(self.message["description"])

    def caption(self):
        return FacebookMessengerMessageBuilder.caption_format.format(caption=self.message["caption"])

    def published_at(self):
        published_at = datetime.datetime.fromtimestamp(timestamp=self.message["published_at_unix_timestamp"])
        published_at = published_at.replace(tzinfo=pytz.utc)
        return published_at.astimezone(pytz.timezone("America/New_York")).strftime("%Y-%m-%d %-I:%M %p")

    def footer(self):
        return FacebookMessengerMessageBuilder.footer_format.format(injury_details=self.injury_details(),
                                                                    published_at=self.published_at())

    def build_messages(self):
        message = self.build()
        if len(message) <= FacebookMessengerMessageBuilder.max_message_length:
            return [message]

        else:
            messages = []
            footer = self.footer()
            message_count = self.expected_message_count()
            sentences = self.description_sentences()
            sentence_index = 0
            # For each message, get sentences that don't go over Facebook's limit
            for message_index in range(0, message_count):
                current_message = self.headline(index=message_index + 1, total_messages=message_count)
                # For the very first message, add the caption
                if message_index == 0:
                    current_message += self.caption()
                message_sentences = []
                # Get the sentences for the current message that don't go over the limit
                # Keep track of the last sentence so that the next message starts from that sentence
                for message_sentence_index in range(sentence_index, len(sentences)):
                    sentence = sentences[message_sentence_index]
                    message_description = " ".join(message_sentences)
                    if len(current_message + message_description + footer) > FacebookMessengerMessageBuilder.max_message_length:
                        break
                    else:
                        message_sentences.append(sentence)
                        sentence_index += 1
                # Separate sentences with a space
                current_message += " ".join(message_sentences)
                # For the last message, add the footer
                if message_index == message_count - 1:
                    current_message += footer
                messages.append(current_message.strip())
            return messages

    def expected_message_count(self):
        message = self.build()
        footer = self.footer()
        return int(math.ceil((len(message) + len(footer)) / FacebookMessengerMessageBuilder.max_message_length))


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