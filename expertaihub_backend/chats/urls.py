# expertaihub_backend/api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ChatMessageListView
from chats.views import ChatSessionViewSet

router = DefaultRouter()
router.register(r'library', ChatSessionViewSet, basename='library')

urlpatterns = [
    # 1) Free‐tier chat endpoint (APIView)

    # 2) Raw messages list endpoint (APIView)
    path(
        "messages/<str:session_id>/",
        ChatMessageListView.as_view(),
        name="chatmessage-list",
    ),

    # 3) All the /api/library/ endpoints come from the router
    path("", include(router.urls)),
]
