

class SubscriptionMessage:
    def __init__(self, platform, platform_identifier, message):
        self.platform = platform
        self.platform_identifier = platform_identifier
        self.message = message