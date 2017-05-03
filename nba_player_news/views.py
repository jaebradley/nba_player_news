from django.http import HttpResponse, HttpResponseForbidden

from environment import FACEBOOK_VERIFY_TOKEN
from models import Subscription


def facebook(request):
    if request.method == "GET":
        if request.GET.get("hub.mode") == "subscribe" and "hub.challenge" in request.GET:
            if not request.GET.get("hub.verify_token") == FACEBOOK_VERIFY_TOKEN:
                return HttpResponseForbidden("Verification token mismatch")
        return HttpResponse(request.GET.get("hub.challenge"))

    if request.method == "POST":
        if request.POST.get("object") == "page":
            for entry in request.POST.get("entry"):
                for message_event in entry["messaging"]:
                    if "message" in message_event:
                        sender_id = message_event["sender"]["id"]
                        recipient_id = message_event["recipient"]["id"]
                        message_text = message_event["message"]["text"]
                        Subscription.objects.create(platform="facebook", platform_identifier=sender_id)

    return HttpResponse("ok")
