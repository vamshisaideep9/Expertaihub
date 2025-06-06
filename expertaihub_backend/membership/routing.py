# chats/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # e.g. ws://<host>/ws/usage/123/
    re_path(r"^ws/usage/(?P<user_id>\d+)/$", consumers.UsageConsumer.as_asgi()),
]
