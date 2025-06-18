# ai_core/management/commands/export_jurisdictions.py

from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
from ai_core.models import DocumentChunk
from itertools import chain

class Command(BaseCommand):
    help = "Export distinct jurisdictions to a TXT file (comma-separated)"

    def handle(self, *args, **options):
        # Query jurisdictions from metadata
        qs = DocumentChunk.objects.values_list('metadata__jurisdiction', flat=True)
        
        # Flatten lists and filter out None/empty values
        jurisdictions = sorted({
            j for j in chain.from_iterable(x for x in qs if x)
        })

        # Join into a comma-separated string
        output_text = ",".join(jurisdictions)

        # Determine output path
        output_path = Path(settings.BASE_DIR) / 'ai_core' / 'jurisdictions.txt'
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_text)

        # Feedback in console
        self.stdout.write(self.style.SUCCESS(
            f"✔ Exported {len(jurisdictions)} jurisdictions to {output_path}"
        ))
