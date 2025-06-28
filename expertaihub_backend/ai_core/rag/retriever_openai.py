#!/usr/bin/env python
"""OpenAI-based retriever utilities."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from functools import lru_cache

try:
    from langchain_openai import OpenAIEmbeddings
except Exception:  # pragma: no cover - optional dependency
    OpenAIEmbeddings = None  # type: ignore

from langchain_core.retrievers import BaseRetriever
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from .retriever_free import SmartQdrantRetriever, _d, _iso_to_ts, LOCAL_URL


EMBED_MODEL = "text-embedding-3-small"


def _embedder() -> "OpenAIEmbeddings":
    if OpenAIEmbeddings is None:
        raise ImportError("langchain_openai package is required for OpenAI retriever")
    return OpenAIEmbeddings(model=EMBED_MODEL, api_key=os.getenv("OPENAI_API_KEY"))


@lru_cache(maxsize=None)
def _load_qdrant_openai(niche: str, country: str) -> tuple[QdrantVectorStore, set[str]]:
    collection = f"{niche.lower()}_{country.lower()}"

    url = os.getenv("QDRANT_URL", "").rstrip("/")
    api_key = os.getenv("QDRANT_API_KEY") or None
    path = os.getenv("QDRANT_LOCAL_PATH") or None

    if url:
        client = QdrantClient(url=url, api_key=api_key, prefer_grpc=False, timeout=120)
    elif path:
        client = QdrantClient(path=path, prefer_grpc=True)
    else:
        client = QdrantClient(url=LOCAL_URL, prefer_grpc=False, timeout=120)

    coll_info = client.get_collection(collection)
    payload_map = set(coll_info.payload_schema or {})
    _d(f"opened collection '{collection}'  keys={payload_map}")

    vs = QdrantVectorStore(
        client=client,
        collection_name=collection,
        embedding=_embedder(),
    )
    return vs, payload_map


def get_retriever_openai(
    niche: str,
    country: str,
    *,
    k: int = 8,
    recency_days: int | None = 365,
    start_date: str | None = None,
    end_date: str | None = None,
    dedupe: bool = True,
) -> BaseRetriever:
    """Return a SmartQdrantRetriever using OpenAI embeddings."""
    start_ts = _iso_to_ts(start_date) if start_date else None
    end_ts = _iso_to_ts(end_date) if end_date else None

    if start_ts is None and recency_days is not None:
        start_ts = int(
            (datetime.now(timezone.utc) - timedelta(days=recency_days)).timestamp()
        )

    vs, keys = _load_qdrant_openai(niche, country)

    return SmartQdrantRetriever(
        vs=vs,
        payload_keys=keys,
        k=k,
        start_ts=start_ts,
        end_ts=end_ts,
        dedupe=dedupe,
    )
