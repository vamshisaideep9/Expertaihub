from django.core.management.base import BaseCommand, CommandError
from ai_core.pipeline.chunk_and_save import chunk_and_save   # the function you just edited

class Command(BaseCommand):
    help = "Chunk RawDocuments and save DocumentChunks"

    def add_arguments(self, parser):
        parser.add_argument("advisor_slug",  help="e.g. immigration")
        parser.add_argument("country_name",  help="e.g. usa")
        parser.add_argument("--force", action="store_true",
                            help="Chunk even if file_hash unchanged")

    def handle(self, *args, **opts):
        advisor = opts["advisor_slug"].lower()
        country = opts["country_name"].lower()
        force   = opts["force"]

        # call the pipeline function with filters
        chunk_and_save(advisor=advisor, country=country, force=force)
