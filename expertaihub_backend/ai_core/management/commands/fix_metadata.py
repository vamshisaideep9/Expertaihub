# ai_core/management/commands/fix_metadata.py
from django.core.management.base import BaseCommand
from django.db import transaction
from ai_core.models import DocumentChunk

class Command(BaseCommand):
    help = "Force niche → 'immigration', country → 'usa' on all chunk metadata"

    def handle(self, *args, **opts):
        qs = DocumentChunk.objects.all()
        self.stdout.write(f"Updating {qs.count()} chunks…")
        with transaction.atomic():
            for chunk in qs.iterator():
                md = chunk.metadata or {}
                md['niche']   = 'immigration'
                md['country'] = 'usa'
                chunk.metadata = md
                chunk.save(update_fields=['metadata'])
        self.stdout.write(self.style.SUCCESS("✅ Done."))
