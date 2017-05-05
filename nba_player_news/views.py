import logging
import logging.config
import os

import redis
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from environment import FACEBOOK_VERIFY_TOKEN, REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME, REDIS_URL

logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "../logger.conf"))
logger = logging.getLogger("views")

client = redis.StrictRedis().from_url(url=REDIS_URL)


@csrf_exempt
def facebook(request):
    if request.method == "GET":
        logger.info("Arguments: {}".format(request.GET))
        if request.GET.get("hub.mode") == "subscribe" and "hub.challenge" in request.GET:
            if not request.GET.get("hub.verify_token") == FACEBOOK_VERIFY_TOKEN:
                return HttpResponseForbidden("Verification token mismatch")
        return HttpResponse(request.GET.get("hub.challenge"))

    if request.method == "POST":
        client.publish(channel=REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME, message=request.body)

    return HttpResponse("ok")
