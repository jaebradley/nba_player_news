# -*- coding: utf-8 -*-
from __future__ import division

import math

from nltk import tokenize


class FacebookMessengerMessageBuilder:

    max_message_length = 640
    message_format = """
    {headline}

    {caption}

    {description}

    {injury_details}
    """

    injury_details_format = """
    Status: {status} | {side} {affected_area} {detail}
    """

    headline_format = """
    {value} ({index}/{total_messages})
    """

    footer_format = """
    {injury_details}
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
            injury_details=self.injury_details())

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

    def footer(self):
        return FacebookMessengerMessageBuilder.footer_format.format(injury_details=self.injury_details())

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
                    message_description = " ".join(message_sentences + [sentence])
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
