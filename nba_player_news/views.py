from django.http import HttpResponse, HttpResponseForbidden

from environment import FACEBOOK_VERIFY_TOKEN


def verify(request):
    if request.method == "GET":
        if request.GET.get("hub.mode") == "subscribe" and "hub.challenge" in request.GET:
            if not request.GET.get("hub.verify_token") == FACEBOOK_VERIFY_TOKEN:
                return HttpResponseForbidden("Verification token mismatch")
        return HttpResponse(request.GET.get("hub.challenge"))

    return HttpResponse("Verification")