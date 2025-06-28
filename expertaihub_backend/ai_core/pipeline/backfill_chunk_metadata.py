#!/usr/bin/env python
"""
ai_core/pipeline/backfill_chunk_meta.py
───────────────────────────────────────
Patch metadata on *existing* DocumentChunk rows
without re-chunking the underlying files.
"""

from __future__ import annotations

import os, sys, re, time, logging, hashlib, random, django
from datetime import datetime
from pathlib import Path
from typing   import List, Iterable

from django.utils     import timezone
from django.db        import transaction, connections, OperationalError
from ai_core.pipeline.chunk_and_save import first_iso_date

# ─── Django bootstrap ──────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "expertaihub_backend.settings")
django.setup()

from ai_core.models import RawDocument, DocumentChunk           # noqa: E402

# ─── logging ───────────────────────────────────────────────────
log = logging.getLogger("chunk_backfill")
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler(sys.stdout))

# ══════════════════════════════════════════════════════════════
#                 Helpers (unchanged) … KEY_TERMS, DATE_PATTERNS,
#                 first_iso_date(), _sha(), _merge() etc.
#                 ↓↓↓ (omitted here for brevity – keep as-is) ↓↓↓
# ══════════════════════════════════════════════════════════════
# … keep your full KEY_TERMS / DATE_PATTERNS / first_iso_date code …

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def now_iso() -> str:
    return timezone.now().isoformat(timespec="seconds").replace("+00:00", "Z")


def _merge(base: dict, patch: dict) -> dict:
    merged = (base or {}).copy()
    for k, v in patch.items():
        if v is not None:
            merged[k] = v
    return merged

# ══════════════════════════════════════════════════════════════
### NEW – utility to iterate queryset in fixed-size pages
def paged(qs, page: int = 250) -> Iterable[List[DocumentChunk]]:
    start = 0
    while True:
        chunk = list(qs[start:start + page])
        if not chunk:
            break
        yield chunk
        start += page
# ══════════════════════════════════════════════════════════════

def backfill_metadata(*, advisor: str = "all", country: str = "all",
                      force: bool = False,
                      page: int = 250,          # chunks per transaction
                      max_retries: int = 4) -> None:
    """
    Update   RawDocument.metadata
    and      DocumentChunk.metadata   in small DB transactions.

    `page` controls how many DocumentChunk rows are patched in one commit.
    """
    log.info("▶ back-fill advisor=%s country=%s page=%s", advisor, country, page)

    # Build base queryset ------------------------------------------------------
    qs_docs = RawDocument.objects.select_related("advisor", "country")
    if advisor.lower() != "all":
        qs_docs = qs_docs.filter(advisor__slug=advisor)
    if country.lower() != "all":
        qs_docs = qs_docs.filter(country__name__iexact=country)

    total_chunks = 0
    for rd in qs_docs.iterator(chunk_size=200):
        print(f"Processing RawDocument id={rd.id}, source_path={rd.source_path}")
        ext = Path(rd.source_path).suffix.lower()
        eff = now_iso()[:10] if ext in {".csv", ".xls", ".xlsx"} else \
              first_iso_date(rd.content, last_modified_fallback=rd.metadata.get("last_modified"))

        # ------------------------------------------------------------------ #
        #  patch its chunks in pages with retry
        # ------------------------------------------------------------------ #
        q_chunks = DocumentChunk.objects.filter(raw_document=rd).order_by("id")
        for page_chunks in paged(q_chunks, page):
            retries = 0
            while True:
                try:
                    with transaction.atomic():
                        for ch in page_chunks:
                            ch.metadata = _merge(ch.metadata, {
                                # Copy from RawDocument metadata:
                                "doc_type":          rd.metadata.get("doc_type"),
                                "jurisdiction_path": rd.metadata.get("jurisdiction_path"),
                                "urls":              rd.metadata.get("urls"),
                                "domains":           rd.metadata.get("domains"),
                                "ner_entities":      rd.metadata.get("ner_entities"),
                                "ingested_at":       rd.metadata.get("ingested_at"),
                                # Add/update effective_date:
                                "effective_date":    eff,
                                # Always update these:
                                "version_hash":      _sha(ch.text),
                                "raw_id":            rd.id,
                                "chunk_index":       ch.chunk_index,
                            })
                        DocumentChunk.objects.bulk_update(
                            page_chunks, ["metadata"], batch_size=page
                        )
                    print(f"  Updated {len(page_chunks)} DocumentChunk metadata for RawDocument id={rd.id}")
                    break  # success – exit retry loop
                except OperationalError as err:
                    if retries >= max_retries:
                        log.error("❌ giving up on RD %s after %s retries – %s",
                                  rd.id, retries, err)
                        raise
                    wait = 2 ** retries + random.random()
                    log.warning("⚠️  DB error (%s). retrying in %.1fs", err, wait)
                    time.sleep(wait)
                    retries += 1
                    # reset connection before retry
                    for conn in connections.all():
                        conn.close_if_unusable_or_obsolete()

            total_chunks += len(page_chunks)

    log.info("✅ patched %s DocumentChunk rows across %s RawDocuments",
             total_chunks, qs_docs.count())


# ─── CLI helper ───────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument("advisor",  help="'all' or advisor slug")
    a.add_argument("country",  help="'all' or country name")
    a.add_argument("--page",   type=int, default=250,
                   help="chunks per DB transaction (default 5 000)")
    a.add_argument("--force",  action="store_true")
    args = a.parse_args()
    backfill_metadata(advisor=args.advisor,
                      country=args.country,
                      force=args.force,
                      page=args.page)
