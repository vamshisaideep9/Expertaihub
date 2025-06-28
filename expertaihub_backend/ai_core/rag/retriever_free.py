#!/usr/bin/env python
"""
retriever_free.py  –  Smart Qdrant retriever for the free tier.

  ✓ Pure-HTTP (Cloud-friendly)
  ✓ Automatic local-Docker fallback
  ✓ Optional recency window (*effective_date*)
  ✓ 3-step search flow  (recency ⟶ all-time ⟶ keyword-fallback + rerank)
  ✓ Duplicate raw-document suppression
  ✓ LRU-cached vector-store (clear with `_load_qdrant.cache_clear()`)
"""

from __future__ import annotations

import os, sys
from datetime      import datetime, timedelta, timezone
from functools     import lru_cache
from typing        import List, Optional, Set, Tuple

from langchain_core.documents  import Document
from langchain_core.retrievers import BaseRetriever
from langchain_huggingface     import HuggingFaceEmbeddings
from langchain_qdrant          import QdrantVectorStore
from qdrant_client             import QdrantClient
from qdrant_client.http        import models as qdj


# ────────────────────────────── Config ──────────────────────────────
EMBED_MODEL   = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_BATCH   = 256
LOCAL_URL     = "http://localhost:6333"
DEBUG_RAG     = bool(os.getenv("DEBUG_RAG"))          # export DEBUG_RAG=1

def _d(msg: str) -> None:
    if DEBUG_RAG:
        print(f"[RAG] {msg}", file=sys.stderr, flush=True)

# single shared embedder (cached by HF transformers)
def _embedder(device: str = "cpu") -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name   = EMBED_MODEL,
        model_kwargs = {"device": device},
        encode_kwargs= {"batch_size": EMBED_BATCH},
    )

def _iso_to_ts(iso: str) -> int:
    dt = datetime.fromisoformat(iso.strip())
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())

# ───────────────────  Vector-store loader (LRU)  ────────────────────
@lru_cache(maxsize=None)
def _load_qdrant(niche: str, country: str) -> tuple[QdrantVectorStore, set[str]]:
    """
    Open the collection and return (LC VectorStore, payload_keys_set).
    Falls back to a local Docker instance if QDRANT_URL/QDRANT_LOCAL_PATH
    are not supplied.
    """
    collection = f"{niche.lower()}_{country.lower()}"

    url     = os.getenv("QDRANT_URL", "").rstrip("/")
    api_key = os.getenv("QDRANT_API_KEY") or None
    path    = os.getenv("QDRANT_LOCAL_PATH") or None

    if url:                                               # Cloud / remote
        client = QdrantClient(url=url, api_key=api_key,
                              prefer_grpc=False, timeout=120)
    elif path:                                            # Embedded RocksDB
        client = QdrantClient(path=path, prefer_grpc=True)
    else:                                                 # Local docker
        client = QdrantClient(url=LOCAL_URL,
                              prefer_grpc=False, timeout=120)

    coll_info   = client.get_collection(collection)
    payload_map = set(coll_info.payload_schema or {})
    _d(f"opened collection '{collection}'  keys={payload_map}")

    vs = QdrantVectorStore(
        client           = client,
        collection_name  = collection,
        embedding        = _embedder("cpu"),
    )
    return vs, payload_map


# ──────────────────────── Retriever class ───────────────────────────
class SmartQdrantRetriever(BaseRetriever):
    """
    1. semantic search with recency filter  (if *effective_date* exists)
    2. semantic search all-time
    3. keyword fallback (MatchText)  ➜  re-rank with cosine similarity
    """

    vs:           QdrantVectorStore
    payload_keys: set[str]
    k:            int
    start_ts:     Optional[int] = None
    end_ts:       Optional[int] = None
    dedupe:       bool          = True

    model_config = {"arbitrary_types_allowed": True}

    # ───────────── helper: date filter ─────────────
    def _date_filter(self) -> qdj.Filter | None:
        if "effective_date" not in self.payload_keys:
            return None
        if self.start_ts is None and self.end_ts is None:
            return None

        def ts2iso(ts: int) -> str:
            return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")

        conds: list[qdj.FieldCondition] = []
        if self.start_ts is not None:
            conds.append(qdj.FieldCondition(
                key="effective_date",
                range=qdj.Range(gte=ts2iso(self.start_ts))
            ))
        if self.end_ts is not None:
            conds.append(qdj.FieldCondition(
                key="effective_date",
                range=qdj.Range(lte=ts2iso(self.end_ts))
            ))
        return qdj.Filter(must=conds)

    # ───────────── helper: keyword filter ──────────
    def _keyword_filter(self, query: str, content_key: str) -> qdj.Filter | None:
        words = [w for w in query.lower().split() if len(w) >= 4]
        if not words:
            return None
        return qdj.Filter(should=[
            qdj.FieldCondition(
                key   = content_key,
                match = qdj.MatchText(value=w)
            )
            for w in words
        ])

    # ───────────── helper: de-duplication ──────────
    def _dedupe(self, docs: List[Document]) -> List[Document]:
        if not self.dedupe:
            return docs[: self.k]

        seen: Set[Tuple[int, int]] = set()
        unique: List[Document]     = []
        for d in docs:
            key = (d.metadata.get("raw_id"), d.metadata.get("chunk_index"))
            if key in seen:
                continue
            unique.append(d)
            seen.add(key)
            if len(unique) == self.k:
                break
        return unique

    # ────────────── core retrieval logic ───────────
    def _get_relevant_documents(self, query: str) -> List[Document]:
        # which payload field holds the text?
        content_key = "page_content" if "page_content" in self.payload_keys else "text"

        # 1️⃣  recency-window semantic search
        docs = self.vs.similarity_search(
            query,
            k=self.k * 3,
            filter=self._date_filter(),
        )
        _d(f"phase-1 recency → {len(docs)} hits")

        # 2️⃣  all-time semantic search
        if not docs:
            docs = self.vs.similarity_search(query, k=self.k * 3)
            _d(f"phase-2 all-time → {len(docs)} hits")

        # 3️⃣  keyword fallback + rerank
        if not docs:
            kw_filter = self._keyword_filter(query, content_key)
            if kw_filter:
                pts, _ = self.vs.client.scroll(
                    self.vs.collection_name,
                    with_payload=True,
                    filter=kw_filter,
                    limit=400,
                )
                if pts:
                    texts = [p.payload.get(content_key, "") for p in pts]
                    emb   = self.vs.embedding_function
                    q_vec = emb.embed_query(query)
                    d_vec = emb.embed_documents(texts)

                    def score(v):  # dot-product (same as cosine on normed vecs)
                        return sum(a * b for a, b in zip(v, q_vec))

                    ranked = sorted(
                        zip(pts, texts, d_vec),
                        key=lambda t: score(t[2]),
                        reverse=True,
                    )[: self.k * 3]

                    docs = [
                        Document(page_content=txt, metadata=pt.payload)
                        for pt, txt, _ in ranked
                    ]
                _d(f"phase-3 keyword → {len(docs)} hits")

        return self._dedupe(docs)


# ────────────────────────── factory API ────────────────────────────
def get_retriever(
    niche: str,
    country: str,
    *,
    k: int = 8,
    recency_days: int | None = 365,
    start_date: str | None   = None,
    end_date:   str | None   = None,
    dedupe: bool = True,
) -> BaseRetriever:
    """
    Return a ready SmartQdrantRetriever.  Call its `.invoke(query)` or
    `.get_relevant_documents(query)`.
    """
    start_ts = _iso_to_ts(start_date) if start_date else None
    end_ts   = _iso_to_ts(end_date)   if end_date   else None

    # default recency window unless explicit dates were provided
    if start_ts is None and recency_days is not None:
        start_ts = int((datetime.now(timezone.utc) - timedelta(days=recency_days)).timestamp())

    vs, keys = _load_qdrant(niche, country)

    return SmartQdrantRetriever(
        vs           = vs,
        payload_keys = keys,
        k            = k,
        start_ts     = start_ts,
        end_ts       = end_ts,
        dedupe       = dedupe,
    )
