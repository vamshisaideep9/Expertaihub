#!/usr/bin/env python
# ai_core/pipeline/data_ingestion.py

import os
import sys
import django
import hashlib
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# ─── Django bootstrap ─────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "expertaihub_backend.settings")
django.setup()
# ────────────────────────────────────────────────────────────────────────────

from django.conf import settings
from ai_core.models import RawDocument, Advisor, Country

logger = logging.getLogger("data_ingestion")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

EXTS = {".pdf", ".docx", ".doc", ".txt", ".csv", ".xlsx", ".xls", ".json"}

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git_commit_for(path: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git","log","-n1","--pretty=format:%H","--", str(path)],
            cwd=PROJECT_ROOT, stderr=subprocess.DEVNULL
        )
        return out.decode().strip()
    except subprocess.CalledProcessError:
        return ""

def ingest(niche_slug: str = "immigration", country_name: str = "usa"):
    docs_root = Path(settings.BASE_DIR) / "documents" / niche_slug / country_name
    if not docs_root.is_dir():
        logger.error(f"No such directory: {docs_root}")
        sys.exit(1)

    try:
        advisor = Advisor.objects.get(slug=niche_slug)
    except Advisor.DoesNotExist:
        logger.error(f"No Advisor with slug='{niche_slug}'")
        sys.exit(1)

    country, created = Country.objects.get_or_create(
        name__iexact=country_name, defaults={"name": country_name}
    )
    if created:
        logger.info(f"Created Country: '{country.name}'")

    logger.info(f"Scanning for docs under {docs_root}")
    processed = 0
    skipped = 0

    for path in docs_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in EXTS:
            continue

        # Compute the unique file hash
        file_hash = sha256(path)

        # If we've already ingested this exact file (by hash), skip it
        if RawDocument.objects.filter(metadata__file_hash=file_hash).exists():
            logger.info(f"Skipping already ingested (hash match): {path.name}")
            skipped += 1
            continue

        # Prepare all the fields for a new RawDocument
        rel_path = str(path.relative_to(Path(settings.BASE_DIR) / "documents"))
        category = str(path.relative_to(docs_root)).rsplit(os.sep, 1)[0]
        filename = path.name
        commit   = git_commit_for(path)
        new_meta = {
            "file_hash":     file_hash,
            "git_commit":    commit,
            "last_modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            "file_type":     path.suffix.lower().lstrip("."),
        }

        # Create the RawDocument
        rd = RawDocument.objects.create(
            source_path=rel_path,
            category=category,
            filename=filename,
            metadata=new_meta,
            content="",     # will fill next
            advisor=advisor,
            country=country,
        )
        logger.info(f"Created RawDocument for {rel_path}")

        # Extract and save full-text
        try:
            suffix = path.suffix.lower()
            if suffix == ".json":
                import json
                data = json.loads(path.read_text(encoding="utf-8"))
                parts = ([data.get("title")] if data.get("title") else []) \
                        + data.get("paragraphs", [])
                text = "\n\n".join(parts).strip()

            elif suffix in {".csv", ".xlsx", ".xls"}:
                import pandas as pd
                df = (pd.read_csv(path) if suffix==".csv"
                      else pd.read_excel(path))
                text = df.to_csv(index=False)

            else:
                from langchain_community.document_loaders import (
                    UnstructuredPDFLoader,
                    UnstructuredWordDocumentLoader,
                    TextLoader
                )
                loader_cls = {
                    ".pdf": UnstructuredPDFLoader,
                    ".docx": UnstructuredWordDocumentLoader,
                    ".doc": UnstructuredWordDocumentLoader
                }.get(suffix, TextLoader)
                loader = loader_cls(file_path=str(path))
                pages = loader.load()
                text = "\n\n".join(p.page_content for p in pages)

            rd.content = text
            rd.save(update_fields=["content"])
            logger.info(f"Ingested content for {rel_path}")
            processed += 1

        except Exception as e:
            logger.warning(f"Failed to extract text for {rel_path}: {e}")

    logger.info(f"✔️ Ingestion complete. Processed={processed}, Skipped={skipped}")

if __name__ == "__main__":
    niche   = sys.argv[1] if len(sys.argv)>1 else "immigration"
    country = sys.argv[2] if len(sys.argv)>2 else "usa"
    ingest(niche, country)
