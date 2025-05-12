from django.db import models
from django.utils.text import slugify
from django.db.models import JSONField

class Advisor(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    

class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    



class RawDocument(models.Model):
    source_path = models.TextField()    # e.g. "documents/immigration/usa/ice/family_residential/FRS-2020.pdf"
    category    = models.TextField()    # e.g. "ice/family_residential"
    filename    = models.CharField(max_length=255)
    content     = models.TextField()    # the full extracted text (or a chunk)
    metadata    = JSONField(default=dict)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category}/{self.filename} ({self.pk})"
    




class DocumentChunk(models.Model):
    raw_document   = models.ForeignKey(RawDocument, on_delete=models.CASCADE, related_name="chunks")
    chunk_index    = models.IntegerField()
    text           = models.TextField()
    metadata       = JSONField()
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("raw_document", "chunk_index")
        indexes = [
            models.Index(fields=["raw_document", "chunk_index"]),
        ]

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.raw_document.filename}"


