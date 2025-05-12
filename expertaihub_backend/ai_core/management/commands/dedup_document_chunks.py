from django.core.management.base import BaseCommand
from ai_core.models import DocumentChunk
from django.db.models import Count

class Command(BaseCommand):
    help = "Remove duplicate DocumentChunk entries (same raw_document, chunk_index, and text)"

    def handle(self, *args, **kwargs):
        duplicates = (
            DocumentChunk.objects
            .values('raw_document_id', 'chunk_index', 'text')
            .annotate(chunk_count=Count('id'))
            .filter(chunk_count__gt=1)
        )

        total_deleted = 0
        for dup in duplicates:
            chunks = (
                DocumentChunk.objects
                .filter(
                    raw_document_id=dup['raw_document_id'],
                    chunk_index=dup['chunk_index'],
                    text=dup['text']
                )
                .order_by('id')
            )
            # keep first, delete rest
            to_delete = chunks[1:]
            count = to_delete.count()
            if count:
                total_deleted += count
                to_delete.delete()

        self.stdout.write(self.style.SUCCESS(f"✅ Removed {total_deleted} duplicate chunks."))
