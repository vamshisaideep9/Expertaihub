#!/usr/bin/env python
import os
import sys
import logging
from pathlib import Path
from datetime import date, timedelta

import django
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

# ─── Django bootstrap ────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "expertaihub_backend.settings")
django.setup()
# ─────────────────────────────────────────────────────────────────

from ai_core.models import DocumentChunk, Advisor, Country
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class Command(BaseCommand):
    help = (
        "Incrementally build/merge a FAISS index of chunk embeddings for the free tier, "
        "parametrized by <niche> (Advisor.slug) and <country> (Country.name)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "niche", type=str,
            help="Advisor slug (e.g. 'immigration')"
        )
        parser.add_argument(
            "country", type=str,
            help="Country name (e.g. 'usa' or 'United States')"
        )
        parser.add_argument(
            "--batch-size", type=int, default=512,
            help="Batch size for embedding"
        )
        parser.add_argument(
            "--vector-root", type=str, default=None,
            help="Base folder for free vectorstores "
                 "(defaults to ai_core/rag/vectorstores/free)"
        )
        parser.add_argument(
            "--device", type=str, default="cpu",
            help="Device for embeddings ('cpu' or 'cuda')"
        )

    def handle(self, *args, **opts):
        niche_slug   = opts["niche"].lower()
        country_name = opts["country"]
        batch_size   = opts["batch_size"]
        device       = opts["device"]

        # 1) Fetch Advisor
        try:
            advisor = Advisor.objects.get(slug=niche_slug)
        except Advisor.DoesNotExist:
            raise CommandError(f"No Advisor found with slug='{niche_slug}'")

        # 2) Fetch or create Country
        country, created = Country.objects.get_or_create(
            name__iexact=country_name,
            defaults={"name": country_name}
        )
        if created:
            self.stdout.write(self.style.WARNING(
                f"ℹ️ Created Country record with name='{country_name}'"
            ))

        # 3) Determine index path
        base = Path(opts["vector_root"]) if opts["vector_root"] else (
            Path(settings.BASE_DIR) / "ai_core" / "rag" / "vectorstores" / "free"
        )
        idx_dir = base / niche_slug / country.name.lower()
        idx_dir.mkdir(parents=True, exist_ok=True)

        # 4) Initialize embedder
        embedder = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": device},
            encode_kwargs={"batch_size": batch_size},
        )

        # 5) Load or start new FAISS index
        if any(idx_dir.iterdir()):
            logger.info("🔄 Loading existing FAISS index...")
            vs = FAISS.load_local(
                str(idx_dir),
                embedder,
                allow_dangerous_deserialization=True
            )
            existing = {
                (doc.metadata.get("raw_id"), doc.metadata.get("chunk_index"))
                for doc in vs.docstore._dict.values()
            }
            logger.info(f"⚡️ Found {len(existing)} existing embeddings")
        else:
            vs = None
            existing = set()
            logger.info("🆕 No existing index — building from scratch")

        # 6) Query chunks for this niche+country
        qs = DocumentChunk.objects.filter(
            raw_document__advisor=advisor,
            raw_document__country=country
        ).order_by("raw_document_id", "chunk_index")

        total_chunks = qs.count()
        to_embed = [
            c for c in qs
            if (c.raw_document_id, c.chunk_index) not in existing
        ]
        logger.info(f"📥 {len(to_embed)} new chunks out of {total_chunks}")

        # 7) Batch-embed & merge
        def chunked(it, size):
            it = iter(it)
            while True:
                batch = []
                try:
                    for _ in range(size):
                        batch.append(next(it))
                except StopIteration:
                    if batch:
                        yield batch
                    break
                yield batch

        for batch in chunked(to_embed, batch_size):
            docs = []
            for chunk in batch:
                logger.info(
                    f"⌛ Embedding chunk raw_id={chunk.raw_document_id} "
                    f"index={chunk.chunk_index}"
                )
                md = chunk.metadata.copy()
                md["raw_id"]      = chunk.raw_document_id
                md["chunk_index"] = chunk.chunk_index
                docs.append(Document(page_content=chunk.text, metadata=md))

            if vs is None:
                logger.info(f"🆕 Embedding initial batch of {len(docs)} chunks")
                vs = FAISS.from_documents(docs, embedder)
            else:
                logger.info(f"➕ Embedding & merging {len(docs)} new chunks")
                new_vs = FAISS.from_documents(docs, embedder)
                vs.merge_from(new_vs)

            for chunk in batch:
                logger.info(
                    f"✅ Finished embedding chunk raw_id={chunk.raw_document_id} "
                    f"index={chunk.chunk_index}"
                )

        # 8) Save updated index
        if vs:
            logger.info(f"💾 Saving FAISS index to {idx_dir}")
            vs.save_local(str(idx_dir))
            self.stdout.write(self.style.SUCCESS(
                "✅ build_vector_store_free complete"
            ))
        else:
            logger.warning(
                "⚠️ No new chunks embedded; index not created/updated"
            )
