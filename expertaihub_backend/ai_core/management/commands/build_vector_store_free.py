#!/usr/bin/env python
"""
( Re-)build a local **Qdrant-lite** collection, adding **only new chunks**.

Usage
-----
$ ./manage.py build_vector_store_free immigration "United States" \
      --batch-size 512 --device cpu
"""

from __future__ import annotations
import logging, os, sys
from pathlib import Path
from typing import Iterable, List, Tuple
from uuid import uuid5, NAMESPACE_DNS             # stable point-IDs

# ── Django bootstrap ───────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "expertaihub_backend.settings")

import django                              # noqa: E402  pylint: disable=wrong-import-position
django.setup()
# ───────────────────────────────────────────────────────────────

from django.conf import settings           # noqa: E402
from django.core.management.base import BaseCommand, CommandError  # noqa: E402

from ai_core.models import Advisor, Country, DocumentChunk          # noqa: E402
from langchain_huggingface import HuggingFaceEmbeddings            # noqa: E402
from langchain_core.documents import Document                      # noqa: E402
from langchain_qdrant import QdrantVectorStore                                # noqa: E402
from qdrant_client import QdrantClient                             # noqa: E402
from qdrant_client.http import models                              # noqa: E402

# ──────────────  logging  ──────────────────────────────────────
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def pid(raw_id: int, chunk_idx: int) -> str:
    """Deterministic point-ID – never duplicates. Returns a valid UUID string."""
    return str(uuid5(NAMESPACE_DNS, f"{raw_id}-{chunk_idx}"))


def batches(qs: Iterable[DocumentChunk],
            seen: set[Tuple[int, int]],
            size: int):
    """Yield *size*-sized batches containing **only unseen** chunks."""
    buf: List[DocumentChunk] = []
    for ch in qs:
        key = (ch.raw_document_id, ch.chunk_index)
        if key in seen:
            continue
        buf.append(ch)
        if len(buf) == size:
            yield buf
            buf = []
    if buf:
        yield buf


# ---------------------------------------------------------------------------
# command
# ---------------------------------------------------------------------------
class Command(BaseCommand):
    help = "Incrementally build / update a local Qdrant-lite (RocksDB) collection."

    def add_arguments(self, p):
        p.add_argument("niche")
        p.add_argument("country")
        p.add_argument("--batch-size", type=int, default=512)
        p.add_argument("--vector-root")
        p.add_argument("--device", default="cpu")

    # ----------------------------------------------------------------------
    def handle(self, *_, **opt):      # noqa: C901  – still okay-length
        niche   = opt["niche"].lower()
        c_name  = opt["country"].strip()
        batch   = opt["batch_size"]
        device  = opt["device"]

        # ── Advisor / Country ───────────────────────────────────────
        try:
            advisor = Advisor.objects.get(slug=niche)
        except Advisor.DoesNotExist as e:
            raise CommandError(f"No Advisor with slug='{niche}'") from e

        country, _ = Country.objects.get_or_create(
            name__iexact=c_name, defaults={"name": c_name},
        )

        # ── storage path ───────────────────────────────────────────
        base = Path(opt["vector_root"] or
                    Path(settings.BASE_DIR) / "ai_core" / "rag" / "vectorstores" / "free")
        db_dir = base / niche / country.name.lower()
        db_dir.mkdir(parents=True, exist_ok=True)

        # ── embeddings ─────────────────────────────────────────────
        embed = HuggingFaceEmbeddings(
            model_name = "sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs = {"device": device},
            encode_kwargs = {"batch_size": batch},
        )

        # ── qdrant client (embedded) ───────────────────────────────
        client = QdrantClient(path=str(db_dir), prefer_grpc=False)
        col = f"{niche}_{country.name.lower()}"

        # create once
        if col not in {c.name for c in client.get_collections().collections}:
            dim = len(embed.embed_query("dim?"))
            log.info("🆕 Creating collection '%s' (dim=%d)", col, dim)
            client.create_collection(
                collection_name   = col,
                vectors_config    = models.VectorParams(size=dim, distance=models.Distance.COSINE),
                optimizers_config = models.OptimizersConfigDiff(indexing_threshold=1_000_000),
            )

        # QUICK-EXIT if nothing new
        db_rows   = (DocumentChunk.objects
                     .filter(raw_document__advisor=advisor,
                             raw_document__country=country)
                     .count())
        pt_count  = client.count(collection_name=col).count
        if pt_count >= db_rows:
            log.info("✨ Up-to-date (%d points == %d DB rows)", pt_count, db_rows)
            return

        # ── already-set (stream once) ──────────────────────────────
        seen: set[Tuple[int, int]] = set()
        cursor = None
        while True:
            pts, cursor = client.scroll(col, with_payload=True, limit=20_000, offset=cursor)
            for p in pts:
                pl = p.payload or {}
                seen.add((pl.get("raw_id"), pl.get("chunk_index")))
            if cursor is None:
                break
        log.info("⚡️  %d chunks already stored", len(seen))

        # ── DB iterator & add only new chunks ──────────────────────
        qs = (DocumentChunk.objects
              .filter(raw_document__advisor=advisor,
                      raw_document__country=country)
              .order_by("raw_document_id", "chunk_index")
              .iterator(chunk_size=1_000))

        vstore = QdrantVectorStore(client=client, collection_name=col, embedding=embed)

        added = 0
        for pack in batches(qs, seen, batch):
            docs, ids = [], []
            for ch in pack:
                meta = ch.metadata | {"raw_id": ch.raw_document_id,
                                      "chunk_index": ch.chunk_index}
                docs.append(Document(page_content=ch.text, metadata=meta))
                ids.append(pid(ch.raw_document_id, ch.chunk_index))

            vstore.add_documents(docs, ids=ids, wait=False)
            added += len(docs)
            log.info("➕  added %d  (total new %d)", len(docs), added)

        log.info("🎉 Finished.  Added %d new chunks.", added)
