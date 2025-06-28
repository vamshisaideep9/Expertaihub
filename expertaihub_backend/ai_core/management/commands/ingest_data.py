# ai_core/management/commands/ingest_data.py

from django.core.management.base import BaseCommand, CommandError
from expertaihub_backend.ai_core.pipeline.data_ingestion import ingest

class Command(BaseCommand):
    help = 'Ingests data into the RawDocument model for a given niche and country'

    def add_arguments(self, parser):
        parser.add_argument(
            'niche',
            type=str,
            help='Advisor slug / niche (e.g. "immigration")'
        )
        parser.add_argument(
            'country',
            type=str,
            help='Country name (e.g. "usa" or "United States")'
        )

    def handle(self, *args, **options):
        niche   = options['niche']
        country = options['country']

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"▶ Starting data ingestion for niche='{niche}' country='{country}'"
        ))
        try:
            ingest(niche, country)
        except Exception as e:
            raise CommandError(f"Data ingestion failed: {e}")

        self.stdout.write(self.style.SUCCESS(
            f"✔️ Successfully ingested data for niche='{niche}' country='{country}'"
        ))
