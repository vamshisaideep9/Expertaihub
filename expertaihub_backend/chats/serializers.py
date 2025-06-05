# chats/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import ChatSession, ChatMessage, Reaction, AccessRequest, FeedbackReason, MessageFeedback
from ai_core.serializers import CountrySerializer, AdvisorSerializer
from ai_core.models import Advisor, Country

User = get_user_model()


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # pick whichever fields you need (full_name, email, avatar…)
        fields = ("id", "email", "full_name")


class ReactionSerializer(serializers.ModelSerializer):
    """
    Create or update a user's reaction (like/dislike) to a ChatMessage.
    """
    class Meta:
        model = Reaction
        fields = ["message", "reaction"]


class ChatMessageSerializer(serializers.ModelSerializer):
    likes_count             = serializers.SerializerMethodField()
    dislikes_count          = serializers.SerializerMethodField()
    user_reaction           = serializers.SerializerMethodField()
    feedback_reason_counts  = serializers.SerializerMethodField()
    user_feedback           = serializers.SerializerMethodField()
    html_content            = serializers.CharField(read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            "id", "session", "role", "content", "html_content", "timestamp",
            "likes_count", "dislikes_count", "user_reaction",
            "feedback_reason_counts", "user_feedback",
        ]

    def get_likes_count(self, obj):
        return obj.reactions.filter(reaction=Reaction.LIKE).count()

    def get_dislikes_count(self, obj):
        return obj.reactions.filter(reaction=Reaction.DISLIKE).count()

    def get_user_reaction(self, obj):
        user = self.context["request"].user
        if not user.is_authenticated:
            return None
        react = obj.reactions.filter(user=user).first()
        return react.reaction if react else None

    def get_feedback_reason_counts(self, obj):
        """
        Return a dict of { reason_value: count } for all reasons.
        """
        counts = {}
        for value, label in FeedbackReason.choices:
            counts[value] = obj.feedbacks.filter(reasons__contains=[value]).count()
        return counts

    def get_user_feedback(self, obj):
        """
        If the current user has submitted feedback on this message,
        return {'reasons': [...], 'additional_comments': '...'}, otherwise None.
        """
        user = self.context["request"].user
        if not user.is_authenticated:
            return None
        fb = obj.feedbacks.filter(user=user).first()
        if not fb:
            return None
        return {
            "reasons": fb.reasons,
            "additional_comments": fb.additional_comments,
        }

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        request = self.context.get("request", None)
        # hide raw counts from non-staff if you like
        if not (request and request.user.is_staff):
            rep.pop("likes_count", None)
            rep.pop("dislikes_count", None)
        return rep


class AccessRequestSerializer(serializers.ModelSerializer):
    """
    Shows who’s requested access to a private session.
    """
    requester = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = AccessRequest
        fields = ["id", "requester", "status", "created"]
        read_only_fields = fields


class ChatSessionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )

    owner_detail = SimpleUserSerializer(source="user", read_only=True)

    advisor = serializers.PrimaryKeyRelatedField(
        queryset=Advisor.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )
    advisor_detail = AdvisorSerializer(source="advisor", read_only=True)

    country = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )
    country_detail = CountrySerializer(source="country", read_only=True)

    # --- NEW FIELDS ---
    share_option  = serializers.ChoiceField(
        choices=ChatSession.SHARE_CHOICES,
        default=ChatSession.SHARE_CHOICES[0][0]
    )
    allowed_users = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True
    )
    access_requests = AccessRequestSerializer(
        many=True,
        read_only=True
    )

    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "user",
            "owner_detail",
            "session_id",
            "slug",
            "advisor",
            "country",
            "advisor_detail",
            "country_detail",
            "pinned",
            "notes",
            "title",
            "archived",
            "completed",
            "created",
            "updated",

            # share fields
            "share_option",
            "allowed_users",
            "access_requests",

            # embedded chat
            "messages",
        ]
        read_only_fields = [
            "id",
            "session_id",
            "created",
            "updated",
            "messages",
            "advisor_detail",
            "country_detail",
            "allowed_users",
            "access_requests",
        ]


class MessageFeedbackSerializer(serializers.ModelSerializer):
    reasons = serializers.ListField(
        child=serializers.ChoiceField(choices=FeedbackReason.choices),
        min_length=1,
        allow_empty=False
    )

    class Meta:
        model = MessageFeedback
        fields = ["id", "user", "message", "reasons", "additional_comments", "created_at"]
        read_only_fields = ["id", "user", "created_at"]