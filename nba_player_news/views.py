import logging
import logging.config
import os
import json

import redis
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from environment import FACEBOOK_VERIFY_TOKEN, REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME, REDIS_URL

logger = logging.getLogger("views")

client = redis.StrictRedis().from_url(url=REDIS_URL)


@csrf_exempt
def facebook(request):
    logger.info("Webhook from Facebook. Method: {} | Query Params: {} | Body: {}"
                .format(request.method, request.GET, request.body))
    if request.method == "GET":
        logger.info("Arguments: {}".format(request.GET))
        if request.GET.get("hub.mode") == "subscribe" and "hub.challenge" in request.GET:
            if not request.GET.get("hub.verify_token") == FACEBOOK_VERIFY_TOKEN:
                return HttpResponseForbidden("Verification token mismatch")
        return HttpResponse(request.GET.get("hub.challenge"))

    if request.method == "POST":
        body = json.loads(request.body)
        body["platform"] = "facebook"
        client.publish(channel=REDIS_SUBSCRIBER_EVENTS_CHANNEL_NAME, message=json.dumps(body))

    return HttpResponse("ok")
