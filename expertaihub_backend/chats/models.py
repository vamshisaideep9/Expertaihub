# chats/models.py
import uuid
from django.db import models
from django.db.models import JSONField
from django.contrib.auth import get_user_model
from ai_core.models import Advisor, Country
from django.contrib.postgres.fields import ArrayField
User = get_user_model()




class ChatSession(models.Model):

    SHARE_CHOICES = [
        ("private", "Private"),
        ("link",    "Anyone with link"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_sessions"
    )
    session_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        help_text="URL-safe identifier for routing/web UI"
    )
    advisor = models.ForeignKey(
        Advisor,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Which domain expert handled this chat"
    )
    country = models.ForeignKey(
        Country,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="User's country context for RAG retrieval"
    )
    pinned = models.BooleanField(
        default=False,
        help_text="Quick-access bookmark flag"
    )
    notes = models.TextField(
        blank=True,
        help_text="Free-text notes or summary"
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Session title (optional)"
    )
    archived = models.BooleanField(
        default=False,
        help_text="Hide completed/old sessions"
    )
    memory_data = JSONField(
        default=list,
        null=True,
        blank=True,
        help_text="Serialized LangGraph memory (chat history, embeddings state, etc.)"
    )
    completed = models.BooleanField(
        default=False,
        help_text="Mark workflow as done"
    )
    created = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
        help_text="When this session was created"
    )
    updated = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True,
        help_text="Last modification timestamp"
    )

    share_option = models.CharField(
        max_length=10, choices=SHARE_CHOICES, default="private"
    )

    allowed_users = models.ManyToManyField(
        User,
        blank=True,
        related_name="shared_sessions",
    )

    def __str__(self):
        return self.title or str(self.session_id)
    



class AccessRequest(models.Model):
    STATUS = [
        ("pending",  "Pending"),
        ("approved", "Approved"),
        ("denied",   "Denied"),
    ]
    session   = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="access_requests")
    requester = models.ForeignKey(User, on_delete=models.CASCADE)
    status    = models.CharField(max_length=10, choices=STATUS, default="pending")
    token     = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)
    created   = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("session", "requester")


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant")
    ]
    session = models.ForeignKey(
        ChatSession,
        related_name="messages",
        on_delete=models.CASCADE
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        help_text="Who sent this message"
    )
    content = models.TextField(
        help_text="The message text"
    )
    html_content = models.TextField(
        blank=True,
        help_text="Pre-rendered HTML of the message"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
        help_text="When the message was sent"
    )

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"[{self.role}] {self.content[:50]}..."
    


class Reaction(models.Model):
    LIKE    = "like"
    DISLIKE = "dislike"
    REACTION_CHOICES = [
        (LIKE,    "Like"),
        (DISLIKE, "Dislike"),
    ]

    user     = models.ForeignKey(User, on_delete=models.CASCADE)
    message  = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name="reactions")
    reaction = models.CharField(max_length=7, choices=REACTION_CHOICES)

    class Meta:
        unique_together = ("user", "message")

class FeedbackReason(models.TextChoices):
    INACCURATE        = "inaccurate",        "Inaccurate"
    TOO_SHORT         = "too_short",         "Too short"
    TOO_LONG          = "too_long",          "Too long"
    OUT_OF_CONTEXT    = "out_of_context",    "Out of context"
    HARMFUL_OFFENSIVE = "harmful_offensive", "Harmful/Offensive"
    OTHER             = "other",             "Other"

class MessageFeedback(models.Model):
    user                = models.ForeignKey(User, on_delete=models.CASCADE)
    message             = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name="feedbacks")
    reasons             = ArrayField(
                            models.CharField(max_length=32, choices=FeedbackReason.choices),
                            size=6,
                        )
    additional_comments = models.TextField(blank=True, null=True)
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


