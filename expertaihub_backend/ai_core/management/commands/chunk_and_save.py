import re
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings

from ai_core.models import RawDocument, DocumentChunk
from langchain.text_splitter import RecursiveCharacterTextSplitter

# tweak these to taste
CHUNK_SIZE    = 800
CHUNK_OVERLAP = 100

def clean_text(text: str) -> str:
    # remove e.g. "Page 3 of 10" footers, excessive hyphens, etc.
    text = re.sub(r"^Page\s+\d+\s+of\s+\d+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"-{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()

def build_metadata(raw: RawDocument) -> dict:
    md = dict(raw.metadata or {})
    rel = raw.source_path.replace("\\", "/")
    parts = rel.split("/")
    md["niche"]   = parts[0]                if len(parts) > 0 else "immigration"
    md["country"] = parts[1]                if len(parts) > 1 else "usa"
    if len(parts) > 3:
        md["category"] = "/".join(parts[2:-1])
    else:
        md["category"] = parts[2] if len(parts) > 2 else ""
    filename = parts[-1]
    md["filename"]  = filename
    md["extension"] = Path(filename).suffix.lower()
    full_path = Path(settings.BASE_DIR) / raw.source_path
    try:
        md["file_size"] = full_path.stat().st_size
    except Exception:
        md["file_size"] = None
    md["source_path"] = rel

    return md

class Command(BaseCommand):
    help = "Clean, chunk RawDocument → DocumentChunk (with enriched metadata)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--chunk-size", type=int, default=CHUNK_SIZE,
            help="Max characters per chunk"
        )
        parser.add_argument(
            "--chunk-overlap", type=int, default=CHUNK_OVERLAP,
            help="Overlap between chunks"
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Just show chunks; don’t write to DB"
        )

    def handle(self, *args, **opts):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=opts["chunk_size"],
            chunk_overlap=opts["chunk_overlap"],
            separators=["\n\n", "\n", " ", ""],
        )

        total = 0
        for raw in RawDocument.objects.iterator():
            base_md = build_metadata(raw)
            cleaned = clean_text(raw.content)
            pieces  = splitter.split_text(cleaned)
            if not opts["dry_run"]:
                DocumentChunk.objects.filter(raw_document=raw).delete()
            for idx, txt in enumerate(pieces):
                chunk_md = {
                    **base_md,
                    "chunk_index": idx,
                    "source_id":    raw.id,
                }

                if opts["dry_run"]:
                    preview = txt[:60].replace("\n", " ")
                    self.stdout.write(f"[{raw.filename} #{idx}] {preview}…")
                else:
                    DocumentChunk.objects.create(
                        raw_document= raw,
                        chunk_index=   idx,
                        text=          txt,
                        metadata=      chunk_md,
                    )
                    total += 1

        if opts["dry_run"]:
            self.stdout.write(self.style.WARNING("⚠️ Dry run complete; no chunks were saved."))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Persisted {total} chunks."))