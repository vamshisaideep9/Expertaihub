from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChatLibraryListView,
    ChatLibraryDetailView,
    ChatSessionViewSet,
    ChatMessageListView,
)

router = DefaultRouter()
router.register(r'library', ChatSessionViewSet, basename='chat-session')

urlpatterns = [
    path('library/list/',      ChatLibraryListView.as_view(),    name='chatlibrary-list'),
    path('library/<slug:slug>/', ChatLibraryDetailView.as_view(), name='chatlibrary-detail'),

    # ← CHANGE: use <str:session_id> so your random 32-char IDs match
    path('messages/<str:session_id>/', ChatMessageListView.as_view(), name='chatmessage-list'),

    path('', include(router.urls)),
]

