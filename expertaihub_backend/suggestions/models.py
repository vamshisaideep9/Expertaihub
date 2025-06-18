from django.db import models
import json
from chats.models import ChatSession

# dimensionality for all embedding vectors
EMBED_DIM = 768

# Create your models here.
class FAQQuestion(models.Model):
    """
    Corpus of real / curated questions.
    """
    text       = models.TextField(unique=True)
    embedding  = models.TextField(null=True, blank=True)  # Store as JSON string
    tier       = models.CharField(max_length=20, default="free")  # free / pro / premium
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:80]
    
    def set_embedding(self, embedding_list):
        """Set embedding as JSON string"""
        if embedding_list is not None:
            self.embedding = json.dumps(embedding_list)
        else:
            self.embedding = None
    
    def get_embedding(self):
        """Get embedding as list"""
        if self.embedding:
            return json.loads(self.embedding)
        return None


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
    embedding = models.TextField(null=True, blank=True)  # Store as JSON string
    rank     = models.PositiveSmallIntegerField()
    clicked  = models.BooleanField(default=False)
    created  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("session", "text")
        ordering = ["rank"]

    def __str__(self):
        return f"#{self.rank} – {self.text[:60]}"
    
    def set_embedding(self, embedding_list):
        """Set embedding as JSON string"""
        if embedding_list is not None:
            self.embedding = json.dumps(embedding_list)
        else:
            self.embedding = None
    
    def get_embedding(self):
        """Get embedding as list"""
        if self.embedding:
            return json.loads(self.embedding)
        return None