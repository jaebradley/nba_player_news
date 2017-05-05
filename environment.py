from os import environ

DATABASE_URL = environ.get("DATABASE_URL")
DEBUG = environ.get("DEBUG")
REDIS_URL=environ.get("REDIS_URL")
SECRET_KEY = environ.get("SECRET_KEY")
REDIS_PLAYER_NEWS_CHANNEL_NAME = environ.get("REDIS_PLAYER_NEWS_CHANNEL_NAME")
REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME = environ.get("REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME")
REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME = environ.get("REDIS_SUBSCRIPTION_MESSAGES_CHANNEL_NAME")
GMAIL_USERNAME = environ.get("GMAIL_USERNAME")
GMAIL_PASSWORD = environ.get("GMAIL_PASSWORD")
TWITTER_CONSUMER_KEY = environ.get("TWITTER_CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = environ.get("TWITTER_CONSUMER_SECRET")
TWITTER_ACCESS_TOKEN = environ.get("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = environ.get("TWITTER_ACCESS_SECRET")
FACEBOOK_PAGE_ACCESS_TOKEN = environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")
FACEBOOK_VERIFY_TOKEN = environ.get("FACEBOOK_VERIFY_TOKEN")