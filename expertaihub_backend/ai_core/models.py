from django.db import models
from django.utils.text import slugify
from django.db.models import JSONField


    

class Country(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    

class Advisor(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    country     = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="advisors",
        null=True, blank=True
    )
    retriever_index = models.CharField(
        max_length=100,
        default="immigration_usa",          # seed value for existing rows
        help_text="Name of the Qdrant collection / index"
    )
    default_tier = models.CharField(
        max_length=10,
        default="free",                     # 'free' | 'plus' | 'pro+'
        help_text="Tier used when caller didn’t pass one"
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    

class RawDocument(models.Model):
    source_path = models.TextField(help_text="Relative path under documents/…")
    category = models.TextField(help_text="High-level folder/category")
    filename = models.CharField(max_length=255)
    content = models.TextField(help_text="The full extracted text of the document")
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    # New fields for long-term filtering
    advisor = models.ForeignKey(
        Advisor,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="raw_documents"
    )
    country = models.ForeignKey(
        Country,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="raw_documents"
    )

    def __str__(self):
        return f"{self.category}/{self.filename} (#{self.pk})"

class DocumentChunk(models.Model):
    raw_document = models.ForeignKey(
        RawDocument,
        on_delete=models.CASCADE,
        related_name="chunks"
    )
    chunk_index = models.IntegerField(help_text="Zero-based index of this chunk")
    text = models.TextField(help_text="The chunk’s plain-text content")
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("raw_document", "chunk_index")
        indexes = [models.Index(fields=["raw_document", "chunk_index"])]

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.raw_document.filename}"