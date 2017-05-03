from django.conf.urls import url
from graphene_django.views import GraphQLView

from views import facebook

urlpatterns = [
    url(r'^graphql', GraphQLView.as_view(graphiql=True)),
    url(r'^facebook', facebook)
]