# chats/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChatSessionCreateView,
    ChatSessionStreamView,
    ChatSessionRunView,
    ChatSessionViewSet,
    ReactionUpsertView, access_request_approve, MessageFeedbackCreateView
)

app_name = "chats"

router = DefaultRouter()
# We register the viewset under the empty string so that when
# we include it at "sessions/" it gives us exactly:
#   GET    /api/sessions/
#   GET    /api/sessions/{slug}/
#   DELETE /api/sessions/{slug}/
#   POST   /api/sessions/{slug}/pin/
#   …etc.
router.register(r"", ChatSessionViewSet, basename="sessions")

urlpatterns = [
    # 1) Custom creation & streaming endpoints first:
    path(
        "sessions/create/",
        ChatSessionCreateView.as_view(),
        name="chat-session-create"
    ),
    path("sessions/<slug:slug>/stream",  ChatSessionStreamView.as_view(), name="chat-session-stream-noslash"),
    path("sessions/<slug:slug>/stream/",  ChatSessionStreamView.as_view(), name="chat-session-stream"),
    path("sessions/<slug:slug>/heartbeat", ChatSessionStreamView.as_view(), name="chat-session-heartbeat"),
    path("sessions/<slug:slug>/run/", ChatSessionRunView.as_view(), name="chat-session-run"),
    
    path(
      "sessions/<slug:slug>/messages/<int:message_id>/react/",
      ReactionUpsertView.as_view(),
      name="message-react"
    ),

    path(
        "access-request/approve/<uuid:token>/",
        access_request_approve,
        name="access_request_approve",
    ),

    path(
      "sessions/<slug:slug>/messages/<int:msg_id>/feedback/",
      MessageFeedbackCreateView.as_view(),
      name="message-feedback-create",
    ),

    # 2) Then all the viewset‐generated routes under /sessions/:
    path("sessions/", include(router.urls)),
]
