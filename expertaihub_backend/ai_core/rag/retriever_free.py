"""
Lightweight Qdrant-lite retriever for "free-tier" vector-stores.

Usage
-----
    from retriever_free import get_retriever
    r = get_retriever("immigration", "usa", k=5)
    docs = r.get_relevant_documents("Can I expedite my I-130?")
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import List, Optional
import sys

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdj

# ────────────────────────────────────────────────────────────────
# CONFIGURATION – adjust only these two constants if you move files
# ────────────────────────────────────────────────────────────────
BASE_STORE = Path(
    r"c:/Users/vamsh/OneDrive/Desktop/ExpertAiHub/Expertaihub/"
    r"expertaihub_backend/ai_core/rag/vectorstores/free"
)
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_BATCH = 256  # suitable for CPU; change if you have GPU

# ────────────────────────────────────────────────────────────────
# helpers
# ────────────────────────────────────────────────────────────────
def _embedder(device: str = "cpu") -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": device},
        encode_kwargs={"batch_size": EMBED_BATCH},
    )


@lru_cache(maxsize=None)
def _load_qdrant(niche: str, country: str) -> QdrantVectorStore:
    """
    Open the local RocksDB collection <niche>_<country> and return
    a LangChain Qdrant vector-store wrapper.
    """
    try:
        print(f"[Qdrant] _load_qdrant called with niche={niche}, country={country}", flush=True)
        niche, country = niche.lower(), country.lower()
        folder = BASE_STORE / niche / country
        print(f"[Qdrant] Folder: {folder}", flush=True)
        collection = f"{niche}_{country}"

        print("[Qdrant] Initializing QdrantClient...", flush=True)
        client = QdrantClient(path=str(folder), prefer_grpc=True)
        print("[Qdrant] QdrantClient initialized.", flush=True)

        
        print("[Qdrant] Listing collections...", flush=True)
        collections = client.get_collections()
        print(f"[Qdrant] Collections: {[c.name for c in collections.collections]}", flush=True)

        if collection not in {c.name for c in collections.collections}:
            print(f"[Qdrant] Collection '{collection}' not found!", flush=True)
            raise FileNotFoundError(
                f'Qdrant collection "{collection}" not found in {folder}.\nRun the build-vector-store command first.'
            )

        print("[Qdrant] Returning Qdrant vector store.", flush=True)
        return QdrantVectorStore(client=client,
                      collection_name=collection,
                      embedding=_embedder("cpu"))
    except Exception as e:
        print(f"[Qdrant][ERROR] Exception in _load_qdrant: {e}", file=sys.stderr, flush=True)
        raise


# ────────────────────────────────────────────────────────────────
# custom retriever
# ────────────────────────────────────────────────────────────────
class DateRangeQdrantRetriever(BaseRetriever):
    """Qdrant-lite retriever with optional date window & de-duplication."""

    vs: QdrantVectorStore
    k: int
    start_iso: Optional[str] = None
    end_iso: Optional[str] = None
    dedupe: bool = True

    class Config:
        arbitrary_types_allowed = True

    # ------------------------------------------------------------------
    def _metadata_filter(self) -> Optional[qdj.Filter]:
        if not (self.start_iso or self.end_iso):
            return None

        conds: list[qdj.FieldCondition] = []
        if self.start_iso:
            conds.append(
                qdj.FieldCondition(
                    key="effective_date",
                    range=qdj.Range(gte=self.start_iso),
                )
            )
        if self.end_iso:
            conds.append(
                qdj.FieldCondition(
                    key="effective_date",
                    range=qdj.Range(lte=self.end_iso),
                )
            )
        return qdj.Filter(must=conds)

    # ------------------------------------------------------------------
    def get_relevant_documents(self, query: str) -> List[Document]:
        print(f"[Retriever] get_relevant_documents called with query: {query}", flush=True)
        try:
            print("[Retriever] Starting similarity search...", flush=True)
            docs = self.vs.similarity_search(
                query,
                k=self.k * 3,               # over-fetch to allow later dedupe
                filter=self._metadata_filter(),
            )
            print(f"[Retriever] Similarity search returned {len(docs)} docs", flush=True)
        except Exception as e:
            print(f"[Retriever][ERROR] Exception during similarity search: {e}", file=sys.stderr, flush=True)
            raise

        if not self.dedupe:
            print(f"[Retriever] Returning first {self.k} docs (no dedupe)", flush=True)
            return docs[: self.k]

        seen, unique = set(), []
        for d in docs:
            rid = d.metadata.get("raw_id")
            if rid not in seen:
                unique.append(d)
                seen.add(rid)
            if len(unique) == self.k:
                break
        print(f"[Retriever] Returning {len(unique)} unique docs after dedupe", flush=True)
        return unique


# ────────────────────────────────────────────────────────────────
# public factory
# ────────────────────────────────────────────────────────────────
def get_retriever(
    niche: str,
    country: str,
    *,
    k: int = 8,
    recency_days: int | None = 365,
    start_date: str | None = None,
    end_date: str | None = None,
    dedupe: bool = True,
) -> BaseRetriever:
    """
    Return a ready-to-use retriever.

    Parameters
    ----------
    niche, country   : collection identifiers
    k                : number of final chunks to return
    recency_days     : if >0 and *start_date* not given,
                       limit to the last N days
    start_date / end_date
                     : ISO-8601 YYYY-MM-DD strings; override recency_days
    dedupe           : drop duplicate raw_documents
    """
    print(f"[Factory] get_retriever called with niche={niche}, country={country}, k={k}, recency_days={recency_days}, start_date={start_date}, end_date={end_date}, dedupe={dedupe}", flush=True)
    print("[Factory] Loading Qdrant collection...", flush=True)
    vs = _load_qdrant(niche, country)
    print("[Factory] Qdrant loaded.", flush=True)

    # work out lower bound for effective_date
    start_iso = start_date
    if not start_iso and recency_days and recency_days > 0:
        start_iso = (date.today() - timedelta(days=recency_days)).isoformat()
    print(f"[Factory] Using start_iso={start_iso}, end_iso={end_date}", flush=True)

    return DateRangeQdrantRetriever(
        vs=vs,
        k=k,
        start_iso=start_iso,
        end_iso=end_date,
        dedupe=dedupe,
    )
