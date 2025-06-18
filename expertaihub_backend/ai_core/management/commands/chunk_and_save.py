from django.core.management.base import BaseCommand, CommandError
from ai_core.pipeline.chunk_and_save import chunk_and_save

class Command(BaseCommand):
    help = (
        "Clean & split RawDocument.content into DocumentChunk rows, "
        "skipping any documents that haven’t changed since last run."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("▶ Starting chunk_and_save…"))
        try:
            chunk_and_save()
        except Exception as e:
            raise CommandError(f"chunk_and_save failed: {e}")
        self.stdout.write(self.style.SUCCESS("✅ chunk_and_save completed successfully"))
