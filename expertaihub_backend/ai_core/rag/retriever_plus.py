#!/usr/bin/env python
"""
retriever_plus.py  –  minimal, timeout-safe Qdrant retriever for PLUS users.

• OpenAI embeddings  (text-embedding-3-small)
• Dynamic collection  "<niche>_<country>_plus"
• Low-EF HNSW search to finish well under Qdrant’s 60-s limit
"""

from __future__ import annotations

import os
from functools import lru_cache

from langchain_openai       import OpenAIEmbeddings
from langchain_qdrant       import QdrantVectorStore
from qdrant_client          import QdrantClient
from qdrant_client.http.models import SearchParams   # ← object, not dict!

# ───────── config ────────────────────────────────────────────────
EMBED_MODEL = "text-embedding-3-small"
LOCAL_URL   = "http://localhost:6333"

# ───────── singleton embedder ────────────────────────────────────
@lru_cache(maxsize=None)
def _embedder() -> OpenAIEmbeddings:            # type: ignore[name-defined]
    return OpenAIEmbeddings(
        model=EMBED_MODEL,
        api_key=os.getenv("OPENAI_API_KEY"),
        request_timeout=30,
    )

# ───────── vector-store factory (LRU) ────────────────────────────
@lru_cache(maxsize=None)
def _vector_store(niche: str, country: str) -> QdrantVectorStore:
    collection = f"{niche.lower()}_{country.lower()}_plus"

    client = QdrantClient(
        url=os.getenv("QDRANT_URL", LOCAL_URL),
        api_key=os.getenv("QDRANT_API_KEY") or None,
        prefer_grpc=False,
        timeout=120,
    )

    return QdrantVectorStore(
        client=client,
        collection_name=collection,
        embedding=_embedder(),
    )

# ───────── public factory (called by workflow) ───────────────────
def get_retriever_openai(
    niche: str,
    country: str,
    *,
    k: int = 8,
    hnsw_ef: int = 16,      # smaller EF → faster, avoids 60-s server cap
    **_ignored,             # keeps signature compatible with free-tier call
):
    vs = _vector_store(niche, country)
    return vs.as_retriever(
        search_kwargs={
            "k": k,
            # **IMPORTANT**: use SearchParams *object* to satisfy Pydantic
            "search_params": SearchParams(hnsw_ef=hnsw_ef, exact=False),
        }
    )

__all__ = ["get_retriever_openai"]
