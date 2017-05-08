web: gunicorn nba_player_news.wsgi --log-file=-
player_news_messages_worker: python manage.py process_player_news_messages
subscriber_messages_worker: python manage.py process_subscriber_messages
subscription_messages_worker: python manage.py process_subscription_messages
all_subscribers_worker: python manage.py all_subscribers
