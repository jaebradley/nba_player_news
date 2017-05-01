from os import environ

DATABASE_URL = environ.get("DATABASE_URL")
DEBUG = environ.get("DEBUG")
REDIS_HOST = environ.get("REDIS_HOST")
REDIS_PORT = environ.get("REDIS_PORT")
SECRET_KEY = environ.get("SECRET_KEY")
REDIS_CHANNEL_NAME = environ.get("REDIS_CHANNEL_NAME")
GMAIL_USERNAME = environ.get("GMAIL_USERNAME")
GMAIL_PASSWORD = environ.get("GMAIL_PASSWORD")
