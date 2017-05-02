# -*- coding: utf-8 -*-

import datetime


class EmailMessageBuilder:

    message_body_format = """
        <h3>{headline}</h3>
        <h4>{caption}</h4>
        <h5>Description</h5>
        <div>{description}</div>
        {injury_details_body}
        <h7>Published At: {published_at}</h7>
    """
    injury_details_body_format = """
        <h5>Injury Details</h5>
        <div>Status: {status} | Affected Area: {affected_area} | Side: {side} | Additional Details: {detail}
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

    Description:
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
            injury_details_body=self.build_injury_details(),
            published_at=datetime.datetime.fromtimestamp(timestamp=self.message["published_at_unix_timestamp"]).isoformat()
        )

    def build_injury_details(self):
        if self.message["injury"]["is_injured"]:
            return TwitterMessageBuilder.injury_details_format.format(
                status=self.message["injury"]["status"],
                affected_area=self.message["injury"]["affected_area"],
                side=self.message["injury"]["side"],
                detail=self.message["injury"]["detail"]
            )

        return ""

