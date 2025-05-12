
# chats/models.py
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils.crypto import get_random_string

from ai_core.models import Advisor, Country 

User = get_user_model()

class ChatSession(models.Model):
    """
    One conversation thread.  
    - session_id & slug are generated once on first save  
    - advisor & country link to your domain models (nullable)  
    - pinned lets users bookmark important sessions  
    - notes is a free-text field they can edit
    """
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_sessions")
    session_id = models.CharField(max_length=32, unique=True, blank=True)
    slug       = models.SlugField(max_length=255, unique=True, blank=True)
    advisor    = models.ForeignKey(Advisor, null=True, blank=True, on_delete=models.SET_NULL, related_name="chat_sessions")
    country    = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL, related_name="chat_sessions")
    pinned     = models.BooleanField(default=False)
    notes      = models.TextField(blank=True)
    title      = models.CharField(max_length=255, blank=True)
    archived   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.session_id:
            self.session_id = get_random_string(32)
        if not self.slug:
            base = slugify(self.title)[:50] if self.title else "chat"
            unique_suffix = uuid.uuid4().hex[:50]
            self.slug = f"{base}-{unique_suffix}"

        super().save(*args, **kwargs)

    def __str__(self):
        display = self.title or self.slug
        return f"{self.user.email} — {display}"


    
class ChatMessage(models.Model):
    """
    One message in a ChatSession, either from the user or from the AI.
    """
    ROLE_CHOICES = [
        ("user", "User"),
        ("ai",   "AI"),
    ]

    session    = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role       = models.CharField(max_length=4, choices=ROLE_CHOICES)
    content    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.session.slug}][{self.role}] {self.content[:50]}…"




