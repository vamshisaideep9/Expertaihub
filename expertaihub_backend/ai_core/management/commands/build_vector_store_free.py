#!/usr/bin/env python
"""
build_vector_store_free.py ─ Incrementally (re)index DocumentChunk rows into a
Qdrant collection that matches the pattern `<niche>_<country>`.

Key points
──────────
* **Idempotent**: skips chunks that already exist (UUID‑v5 on `<raw_id>-<chunk_index>`)
* **Free‑tier safe**: 
  • limits every upsert to ≤128 vectors (≈50 kB) to avoid 502/timeout drops
  • wraps each upsert in a quick retry on transient HTTP disconnects
* **Minimal metadata**: keeps only the fields we actually query on.
* **Automatic collection bootstrap** with correct vector dimension and a
  string index on `effective_date` (for recency filtering).

Run:
────
```bash
docker compose exec backend \
  python manage.py build_vector_store_free immigration usa --batch-size 128
```
(use any adviser slug / country name present in your DB)
"""
from __future__ import annotations

import os
import sys
import time
import logging
from uuid import uuid5, NAMESPACE_DNS
from pathlib import Path
from typing import Iterable, List, Tuple, Generator

# ── Django bootstrap ────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "expertaihub_backend.settings")
import django  # noqa: E402

django.setup()
# ────────────────────────────────────────────────────────────────

from django.conf import settings  # noqa: E402
from django.core.management.base import BaseCommand, CommandError  # noqa: E402
from ai_core.models import Advisor, Country, DocumentChunk  # noqa: E402
from langchain_huggingface import HuggingFaceEmbeddings  # noqa: E402
from langchain_qdrant import QdrantVectorStore  # noqa: E402
from langchain_core.documents import Document  # noqa: E402
from qdrant_client import QdrantClient  # noqa: E402
from qdrant_client.http import models  # noqa: E402
from httpx import RemoteProtocolError  # type: ignore

# ── logging ─────────────────────────────────────────────────────
log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ═══════════════════════════════════════════════════════════════
# Helper utilities
# ═══════════════════════════════════════════════════════════════

def point_uuid(raw_id: int, chunk_idx: int) -> str:
    """Deterministic UUID‑v5 from `(raw_id, chunk_idx)`."""
    return str(uuid5(NAMESPACE_DNS, f"{raw_id}-{chunk_idx}"))


def chunk_batches(
    qs: Iterable[DocumentChunk], *, already: set[str], size: int
) -> Generator[List[Tuple[DocumentChunk, str]], None, None]:
    """Yield lists of (chunk,row‑uuid) skipping ones that are already stored."""
    buf: List[Tuple[DocumentChunk, str]] = []
    for ch in qs:
        uid = point_uuid(ch.raw_document_id, ch.chunk_index)
        if uid in already:
            continue
        buf.append((ch, uid))
        if len(buf) == size:
            yield buf
            buf = []
    if buf:
        yield buf


# ═══════════════════════════════════════════════════════════════
# Management command
# ═══════════════════════════════════════════════════════════════
class Command(BaseCommand):
    help = "Build / update a Qdrant collection on the free tier (HTTP only)"

    def add_arguments(self, parser):
        parser.add_argument("niche")
        parser.add_argument("country")
        parser.add_argument("--batch-size", type=int, default=256)
        parser.add_argument("--device", default="cpu")

    # ──────────────────────────────────────────────────────────
    def handle(self, *_, **opt):  # noqa: C901
        niche = opt["niche"].lower()
        country = opt["country"].strip().lower()
        batch_cfg = max(1, opt["batch_size"])
        # Hard‑cap the *actual* HTTP batch so one body ≲50 kB
        SAFE_BATCH = min(batch_cfg, 128)
        device = opt["device"]

        # Advisor / Country validation
        try:
            advisor = Advisor.objects.get(slug=niche)
        except Advisor.DoesNotExist:
            raise CommandError(f"Unknown advisor slug: {niche}")

        country_obj, _ = Country.objects.get_or_create(
            name__iexact=country, defaults={"name": country}
        )

        # Embeddings loader
        embedder = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": device},
            encode_kwargs={"batch_size": SAFE_BATCH},
        )

        # Qdrant client (HTTP‑only)
        client = QdrantClient(
            url=getattr(settings, "QDRANT_URL", "http://localhost:6333"),
            api_key=getattr(settings, "QDRANT_API_KEY", None),
            prefer_grpc=False,
            timeout=120,
        )

        collection = f"{niche}_{country}"

        # ── bootstrap collection if absent ────────────────────
        if collection not in {c.name for c in client.get_collections().collections}:
            dim = len(embedder.embed_query("probe"))
            log.info("🆕 creating collection %s (dim=%d)", collection, dim)
            client.create_collection(
                collection_name=collection,
                vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
                optimizers_config=models.OptimizersConfigDiff(indexing_threshold=1_000_000),
            )
        # ensure string index on effective_date
        try:
            client.create_payload_index(
                collection_name=collection,
                field_name="effective_date",
                field_schema=models.PayloadIndexSchemaType.keyword,
            )
        except Exception:
            pass  # already indexed

        # ── figure out work to do ─────────────────────────────
        total_rows = DocumentChunk.objects.filter(
            raw_document__advisor=advisor, raw_document__country=country_obj
        ).count()
        stored = client.count(collection).count
        if stored >= total_rows:
            log.info("✨ collection up‑to‑date (%d points == %d rows)", stored, total_rows)
            return

        # ── gather existing UUIDs (so we can resume) ───────────
        seen: set[str] = set()
        cursor = None
        while True:
            pts, cursor = client.scroll(collection, with_payload=False, limit=20_000, offset=cursor)
            seen.update(p.id for p in pts)
            if cursor is None:
                break
        log.info("⚡️ %d chunks already stored", len(seen))

        # ── iterate DB rows in order ───────────────────────────
        qs = (
            DocumentChunk.objects
            .filter(raw_document__advisor=advisor, raw_document__country=country_obj)
            .order_by("raw_document_id", "chunk_index")
            .iterator(chunk_size=1_000)
        )

        vstore = QdrantVectorStore(client=client, collection_name=collection, embedding=embedder)

        added = 0
        for pack in chunk_batches(qs, already=seen, size=SAFE_BATCH):
            docs, ids = [], []
            for ch, uid in pack:
                meta = ch.metadata | {
                    "raw_id": ch.raw_document_id,
                    "chunk_index": ch.chunk_index,
                }
                docs.append(Document(page_content=ch.text, metadata=meta))
                ids.append(uid)

            # robust upsert with retry on RemoteProtocolError
            for attempt in range(3):
                try:
                    vstore.add_documents(docs, ids=ids, wait=True)
                    break
                except RemoteProtocolError:
                    if attempt == 2:
                        raise
                    log.warning("🔁 HTTP drop – retrying pack (%d/%d)", attempt + 1, 3)
                    time.sleep(2)

            added += len(docs)
            log.info("➕ added %d  (running total %d)", len(docs), added)

        log.info("🎉 finished – appended %d new chunks (collection ≈ %d)", added, stored + added)
