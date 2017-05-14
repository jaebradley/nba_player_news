import json


class SubscriptionMessage:
    def __init__(self, platform, platform_identifier, text):
        self.platform = platform
        self.platform_identifier = platform_identifier
        self.text = text

    def to_json(self):
        return json.dumps({
            "platform": self.platform,
            "platform_identifier": self.platform_identifier,
            "text": self.text
        })

    def __unicode__(self):
        return "Platform: {} | Platform Identifier: {} | Text: {}"\
            .format(self.platform, self.platform_identifier, self.text)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__

        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self.__eq__(other)

        return NotImplemented

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))
