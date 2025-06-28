# ai_core/management/commands/backfill_chunk_meta.py
from django.core.management.base import BaseCommand, CommandError
from ai_core.pipeline.backfill_chunk_metadata import backfill_metadata  # adjust the import
                                                               # path if you placed
                                                               # the function
                                                               # elsewhere

class Command(BaseCommand):
    """
    Usage examples
    --------------

    # patch all chunks for the USA-Immigration advisor
    $ docker compose exec backend \
        python manage.py backfill_chunk_meta immigration usa

    # same, but re-build even if chunked_file_hash unchanged
    $ python manage.py backfill_chunk_meta immigration usa --force
    """

    help = "Back-fill effective_date + other parent-document metadata onto "\
           "all existing DocumentChunk rows."

    def add_arguments(self, parser):
        parser.add_argument("advisor",
                            help="Advisor slug (e.g. 'immigration')")
        parser.add_argument("country",
                            help="Country name as stored in Country.name "\
                                 "(e.g. 'usa')")
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help="Re-run even when RawDocument.chunked_file_hash is unchanged",
        )

    def handle(self, *args, **options):
        advisor  = options["advisor"]
        country  = options["country"]
        force    = options["force"]

        try:
            backfill_metadata(advisor=advisor, country=country, force=force)
        except Exception as exc:
            raise CommandError(str(exc)) from exc
