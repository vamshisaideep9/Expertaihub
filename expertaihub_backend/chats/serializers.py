# chats/serializers.py
from rest_framework import serializers
from ai_core.serializers import AdvisorSerializer, CountrySerializer
from .models import ChatSession, ChatMessage

class ChatMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for individual chat messages.
    """
    class Meta:
        model = ChatMessage
        fields = ("role", "content", "created_at")


class ChatSessionSerializer(serializers.ModelSerializer):
    """
    Summary‐level serializer for listing sessions.
    """
    advisor    = AdvisorSerializer(read_only=True)
    country    = CountrySerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    message_count = serializers.IntegerField(source="messages.count", read_only=True)

    class Meta:
        model  = ChatSession
        fields = [
            "session_id",
            "slug",
            "title",
            "advisor",
            "country",
            "pinned",
            "archived",
            "created_at",
            "updated_at",
            "message_count",
            "last_message",
        ]

    def get_last_message(self, obj):
        msg = obj.messages.order_by("-created_at").first()
        return ChatMessageSerializer(msg).data if msg else None


class ChatSessionDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for a single session, including all messages.
    """
    advisor  = AdvisorSerializer(read_only=True)
    country  = CountrySerializer(read_only=True)
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model  = ChatSession
        fields = [
            "session_id",
            "slug",
            "title",
            "advisor",
            "country",
            "pinned",
            "notes",
            "archived",
            "created_at",
            "updated_at",
            "messages",
        ]
