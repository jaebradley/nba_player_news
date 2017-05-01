# -*- coding: utf-8 -*-

import datetime


class EmailMessageBuilder:

    message_body_format = """
        <h3>{headline}</h3>
        <h4>{caption}</h4>

        <h5>Description</h5>
        <div>
          {description}
        </div>

        {injury_details_body}

        <h7>Player: {first_name} {last_name} playing {position} for the {team}</h7>

        <h7>Published At: {published_at}</h7>
    """
    injury_details_body_format = """
        <h5>Injury</h5>
        <ul>
          <li>
            Status: {status}
          </li>
          <li>
            Affected Area: {affected_area}
          </li>
          <li>
            Side: {side}
          </li>
          <li>
            Additional Details: {detail}
          </li>
        </ul>
    """

    def __init__(self, message):
        self.message = message

    def build(self):
        injury_details_body = ""
        if self.message.injury.is_injured:
            injury_details_body = self.build_injury_details_body()

        return EmailMessageBuilder.message_body_format.format(
            headline=self.message.headline,
            caption=self.message.caption,
            description=self.message.description,
            injury_details_body=injury_details_body,
            first_name=self.message.first_name,
            last_name=self.message.last_name,
            position=self.message.position,
            team=self.message.team,
            published_at=datetime.datetime.utcfromtimestamp(timestamp=self.message.published_at)
        )

    def build_injury_details_body(self):
        return EmailMessageBuilder.injury_details_body_format.format(
            status=self.message.injury.status,
            affected_area=self.message.injurys.affected_area,
            side=self.message.injury.side,
            details=self.message.injury.detail
        )
