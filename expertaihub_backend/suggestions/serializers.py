from rest_framework import serializers
from .models import ChatSuggestion


class ChatSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSuggestion
        fields = ("id", "text", "rank", "clicked")


__all__ = ["ChatSuggestionSerializer"]

