import logging
import logging.config
import os
import json

from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from environment import FACEBOOK_VERIFY_TOKEN
from models import Subscription
from nba_player_news.data.senders import FacebookMessager

logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "../logger.conf"))
logger = logging.getLogger("views")


@csrf_exempt
def facebook(request):
    if request.method == "GET":
        logger.info("Arguments: {}".format(request.GET))
        if request.GET.get("hub.mode") == "subscribe" and "hub.challenge" in request.GET:
            if not request.GET.get("hub.verify_token") == FACEBOOK_VERIFY_TOKEN:
                return HttpResponseForbidden("Verification token mismatch")
        return HttpResponse(request.GET.get("hub.challenge"))

    if request.method == "POST":
        body = json.loads(request.body)
        logger.info("Arguments: {}".format(body))
        if body.get("object") == "page":
            for entry in body.get("entry"):
                for message_event in entry["messaging"]:
                    if "message" in message_event:
                        sender_id = message_event["sender"]["id"]
                        recipient_id = message_event["recipient"]["id"]
                        message_text = message_event["message"]["text"]
                        logger.info("Sender: {} | Recipient: {} | Message: {}".format(sender_id, recipient_id, message_text))
                        if message_text.lower() == "subscribe":
                            Subscription.objects.get_or_create(platform="facebook", platform_identifier=sender_id)
                            FacebookMessager().send(recipient_id=recipient_id, message="You are now subscribed")

    return HttpResponse("ok")
