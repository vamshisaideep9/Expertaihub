from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from ai_core.models import Advisor, Country
from django.utils.crypto import get_random_string
import uuid

User = get_user_model()
# Create your models here.
class ChatSession(models.Model):
    session_id = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        help_text="Opaque identifier for this chat session"
    )

    # User + context
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_sessions"
    )
    advisor  = models.ForeignKey(
        Advisor,
        on_delete=models.SET_NULL,
        null=True
    )
    country  = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True
    )
    slug     = models.SlugField(
        max_length=100,
        unique=True,
        editable=False
    )
    title = models.CharField(
        max_length=100,
        blank=True,
        help_text="Custom name for this chat"
    )
    notes = models.TextField(
        blank=True,
        help_text="Personal notes about this session"
    )
    pinned = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Star / favorite this session"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.session_id:
            self.session_id = get_random_string(32)
        if not self.slug:
            base = slugify(self.title)[:50] if self.title else "chat"
            unique_suffix = uuid.uuid4().hex[:15]
            self.slug = f"{base}-{unique_suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} — {self.title or 'Chat Session'}"

    

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10, choices=[("user", "User"), ("ai", "AI")])
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.upper()} - {self.timestamp}"


class ChatLibrary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="library")
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, null=True, blank=True) 
    prompt = models.TextField()
    answer = models.TextField()
    slug = models.SlugField(unique=True)
    advisor = models.ForeignKey(Advisor, on_delete=models.SET_NULL, null=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.prompt[:30]}"

