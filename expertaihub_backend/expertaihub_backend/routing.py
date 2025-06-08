# expertaihub_backend/routing.py

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import membership.routing
from .asgi import django_asgi_app

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            membership.routing.websocket_urlpatterns
        )
    ),
})
