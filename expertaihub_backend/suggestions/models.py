from django.db import models
from chats.models import ChatSession


# Create your models here.
class FAQQuestion(models.Model):
    """
    Corpus of real / curated questions.
    """
    text       = models.TextField(unique=True)
    tier       = models.CharField(max_length=20, default="free")  # free / pro / premium
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:80]
    


class ChatSuggestion(models.Model):
    """
    One of the five follow-ups shown after each answer.
    Lives in its own app but points back to chats.ChatSession.
    """
    # use a *string* FK to avoid circular import
    session  = models.ForeignKey(
        ChatSession,
        related_name="suggestions",
        on_delete=models.CASCADE,
    )
    text     = models.CharField(max_length=500)
    rank     = models.PositiveSmallIntegerField()
    clicked  = models.BooleanField(default=False)
    created  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("session", "text")
        ordering = ["rank"]

    def __str__(self):
        return f"#{self.rank} – {self.text[:60]}"