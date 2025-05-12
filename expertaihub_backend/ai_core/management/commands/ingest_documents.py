from django.core.management.base import BaseCommand
from django.db import transaction
from ai_core.models import RawDocument
from langchain_community.document_loaders import (
    UnstructuredPDFLoader,
    UnstructuredWordDocumentLoader,
    TextLoader,
)
from langchain.schema import Document
from pathlib import Path

EXT_TO_LOADER = {
    ".pdf": UnstructuredPDFLoader,
    ".docx": UnstructuredWordDocumentLoader,
    ".doc":  UnstructuredWordDocumentLoader,
    ".txt":  TextLoader,
}

class Command(BaseCommand):
    help = (
        "Re-load all files (except JSON) under documents/immigration/usa, "
        "and update content + metadata in RawDocument (matching on source_path)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--root",
            type=str,
            default="documents/immigration/usa",
            help="Root folder to scan"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Don't save to DB, just print what would be loaded",
        )

    def handle(self, *args, **options):
        root = Path(options["root"])
        dry = options["dry_run"]
        niche = root.parent.name
        country = root.name

        processed = 0
        skipped = 0

        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue

            ext = file_path.suffix.lower()
            loader_cls = EXT_TO_LOADER.get(ext)
            if not loader_cls:
                skipped += 1
                continue
            rel = file_path.relative_to(root)
            category = "/".join(rel.parts[:-1])

            self.stdout.write(f"→ Processing {rel}")
            try:
                loader = loader_cls(str(file_path))
                docs: list[Document] = loader.load()
            except Exception as e:
                self.stderr.write(f"  ⚠️ Failed to load {rel}: {e}")
                skipped += 1
                continue

            for doc in docs:
                processed += 1

                md = {
                    **doc.metadata,
                    "source_path": str(rel),
                    "category": category,
                    "filename": file_path.name,
                    "extension": ext,
                    "niche": niche,
                    "country": country,
                    "file_size": file_path.stat().st_size,
                }

                if dry:
                    preview = doc.page_content[:80].replace("\n", " ")
                    self.stdout.write(f"    • [{file_path.name}] {preview}…")
                else:
                    with transaction.atomic():
                        obj, created = RawDocument.objects.update_or_create(
                            source_path=str(rel),
                            filename=file_path.name,
                            defaults={
                                "content": doc.page_content,
                                "metadata": md,
                                "category": category,
                            }
                        )
                        mark = "✓" if created else "↻"
                        self.stdout.write(f"    {mark} {file_path.name}")

        self.stdout.write(self.style.SUCCESS(
            f"Skipped {skipped} files; {'would have processed' if dry else 'processed'} {processed} document chunks."
        ))