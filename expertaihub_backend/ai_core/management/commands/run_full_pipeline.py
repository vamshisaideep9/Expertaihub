# ai_core/management/commands/run_full_pipeline.py

import sys
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

class Command(BaseCommand):
    help = (
        "Run the full pipeline for a given niche+country:\n"
        "  1) ingest_data <niche> <country>\n"
        "  2) chunk_and_save\n"
        "  3) build_vector_store_free <niche>\n\n"
        "Note: build_vector_store_free derives country from the Advisor."
    )

    def add_arguments(self, parser):
        parser.add_argument("niche", type=str,
                            help="Advisor slug (e.g. 'immigration')")
        parser.add_argument("country", type=str,
                            help="Country name (e.g. 'usa' or 'United States')")
        parser.add_argument("--batch-size", type=int, default=None,
                            help="Batch size override for build_vector_store_free")
        parser.add_argument("--vector-root", type=str, default=None,
                            help="Vector-root override for build_vector_store_free")
        parser.add_argument("--device", type=str, default=None,
                            help="Device override for build_vector_store_free")

    def handle(self, *args, **opts):
        niche   = opts["niche"]
        country = opts["country"]

        # 1) ingest_data
        self.stdout.write(self.style.MIGRATE_HEADING(f"1/3 ▶ Ingesting documents for {niche}/{country}"))
        try:
            call_command("ingest_data", niche, country)
        except CommandError as e:
            raise CommandError(f"❌ ingest_data failed: {e}")

        # 2) chunk_and_save
        self.stdout.write(self.style.MIGRATE_HEADING("2/3 ▶ Chunking & saving documents"))
        try:
            call_command("chunk_and_save")
        except CommandError as e:
            raise CommandError(f"❌ chunk_and_save failed: {e}")

        # 3) build_vector_store_free
        self.stdout.write(self.style.MIGRATE_HEADING("3/3 ▶ Building free vectorstore"))
        build_args = [niche, country]
        if opts["batch_size"] is not None:
            build_args += ["--batch-size", str(opts["batch_size"])]
        if opts["vector_root"]:
            build_args += ["--vector-root", opts["vector_root"]]
        if opts["device"]:
            build_args += ["--device", opts["device"]]

        try:
            call_command("build_vector_store_free", *build_args)
        except CommandError as e:
            raise CommandError(f"❌ build_vector_store_free failed: {e}")

        self.stdout.write(self.style.SUCCESS("✅ Full pipeline completed successfully!"))
