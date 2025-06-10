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
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    reason  = serializers.ChoiceField(
        choices=Reaction.LIKE_REASON_CHOICES + Reaction.DISLIKE_REASON_CHOICES,
        required=False,
        allow_blank=True,
    )
    comment = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Reaction
        fields = ["user", "message", "reaction", "reason", "comment"]
        validators = []

    def validate(self, data):
        reason  = data.get("reason", "").strip()
        comment = data.get("comment", "").strip()

        # if no reason provided, skip all further validation
        if not reason:
            return data

        # pick the correct lookup table
        valid = dict(Reaction.LIKE_REASON_CHOICES) if data["reaction"] == Reaction.LIKE else dict(Reaction.DISLIKE_REASON_CHOICES)
        if reason not in valid:
            raise serializers.ValidationError({"reason": f"Invalid reason for '{data['reaction']}'."})

        # if they chose “Other…”, require a non-empty comment
        if reason in {Reaction.LIKE_OTHER, Reaction.DIS_OTHER} and not comment:
            raise serializers.ValidationError({"comment": "Please explain what “Other…” means."})

        return data

    def create(self, validated_data):
        # fill in defaults so we never KeyError
        reason  = validated_data.get("reason", "")
        comment = validated_data.get("comment", "")

        obj, _ = Reaction.objects.update_or_create(
            user=validated_data["user"],
            message=validated_data["message"],
            defaults={
                "reaction": validated_data["reaction"],
                "reason":    reason,
                "comment":   comment,
            },
        )
        return obj


class ChatMessageSerializer(serializers.ModelSerializer):
    likes_count             = serializers.SerializerMethodField()
    dislikes_count          = serializers.SerializerMethodField()
    user_reaction           = serializers.SerializerMethodField()
    reaction_reason_counts  = serializers.SerializerMethodField()
    user_reaction_detail    = serializers.SerializerMethodField()
    feedback_reason_counts  = serializers.SerializerMethodField()
    user_feedback           = serializers.SerializerMethodField()
    html_content            = serializers.CharField(read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            "id", "session", "role", "content", "html_content", "timestamp",
            "likes_count", "dislikes_count", "user_reaction",
            "reaction_reason_counts", "user_reaction_detail",
            "feedback_reason_counts", "user_feedback",
            ]
        read_only_fields = ["id", "session", "role", "timestamp"]

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
    

    def get_reaction_reason_counts(self, obj):
        # Count how many users picked each reason for both likes & dislikes
        counts = {}
        choices = list(Reaction.LIKE_REASON_CHOICES) + list(Reaction.DISLIKE_REASON_CHOICES)
        for key, _ in choices:
            counts[key] = obj.reactions.filter(reason=key).count()
        return counts

    def get_user_reaction_detail(self, obj):
        # Return my full reaction record (type, reason & comment)
        user = self.context["request"].user
        if not user.is_authenticated:
            return None
        react = obj.reactions.filter(user=user).first()
        if not react:
            return None
        return {
            "reaction": react.reaction,
            "reason":   react.reason,
            "comment":  react.comment,
        }

    def get_feedback_reason_counts(self, obj):
        counts = {}
        for value, _ in FeedbackReason.choices:
            counts[value] = obj.feedbacks.filter(reasons__contains=[value]).count()
        return counts

    def get_user_feedback(self, obj):
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
        request = self.context.get("request")
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

