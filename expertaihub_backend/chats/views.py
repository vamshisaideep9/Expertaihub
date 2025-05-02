from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from chats.models import ChatLibrary, ChatSession, ChatMessage
from chats.serializers import ChatLibrarySerializer, ChatSessionSerializer, ChatMessageSerializer

class ChatLibraryListView(ListAPIView):
    serializer_class   = ChatLibrarySerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return ChatLibrary.objects.filter(user=self.request.user).order_by("-created_at")

class ChatLibraryDetailView(RetrieveAPIView):
    serializer_class   = ChatLibrarySerializer
    permission_classes = [IsAuthenticated]
    lookup_field       = "slug"
    def get_queryset(self):
        return ChatLibrary.objects.filter(user=self.request.user)

class ChatSessionViewSet(viewsets.ModelViewSet):
    serializer_class   = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field       = 'slug'
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields   = ['advisor','country']
    search_fields      = ['title','notes']
    ordering_fields    = ['created_at','updated_at']
    ordering           = ['-updated_at']
    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)

class ChatMessageListView(ListAPIView):
    serializer_class   = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        sid = self.kwargs["session_id"]
        return ChatMessage.objects.filter(
            session__session_id=sid,
            session__user=self.request.user
        ).order_by("created_at")
