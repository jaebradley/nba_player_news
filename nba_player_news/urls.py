from django.conf.urls import url
from graphene_django.views import GraphQLView

from views import verify

urlpatterns = [
    url(r'^graphql', GraphQLView.as_view(graphiql=True)),
    url(r'^verify', verify)
]