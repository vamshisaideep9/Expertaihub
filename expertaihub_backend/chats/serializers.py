from rest_framework import serializers
from .models import ChatLibrary, ChatMessage, ChatSession

class ChatLibrarySerializer(serializers.ModelSerializer):
    session_id = serializers.CharField(source="session.session_id", read_only=True)
    advisor    = serializers.CharField(source="advisor.name",  read_only=True)
    country    = serializers.CharField(source="country.code",  read_only=True)

    class Meta:
        model = ChatLibrary
        fields = ["slug", "prompt", "answer", "advisor", "country", "session_id", "created_at"]


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["sender", "content"]


class ChatSessionSerializer(serializers.ModelSerializer):
    advisor = serializers.CharField(source="advisor.name", read_only=True)
    country = serializers.CharField(source="country.code", read_only=True)

    class Meta:
        model = ChatSession
        fields = ["slug", "session_id", "title", "notes", "advisor", "country", "created_at", "updated_at"]
