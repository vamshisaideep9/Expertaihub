import os
from functools import lru_cache
from datetime import date, timedelta
from typing import Optional, List

from django.conf import settings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document, BaseRetriever

# Set PyTorch to use CPU to avoid meta tensor issues
os.environ["CUDA_VISIBLE_DEVICES"] = ""

BASE_VECTORSTORE_FOLDER = os.path.join(
    settings.BASE_DIR, "ai_core", "rag", "vectorstores", "free"
)

@lru_cache(maxsize=None)
def _load_vectorstore(niche: str, country: str) -> FAISS:
    path = os.path.join(BASE_VECTORSTORE_FOLDER, niche.lower(), country.lower())
    if not os.path.isdir(path):
        raise FileNotFoundError(f"No vectorstore at '{path}'")
    
    try:
        embedder = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"device": "cpu"},
        )
        return FAISS.load_local(str(path), embedder, allow_dangerous_deserialization=True)
    except NotImplementedError as e:
        if "meta tensor" in str(e).lower():
            embedder = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
            )
            return FAISS.load_local(str(path), embedder, allow_dangerous_deserialization=True)
        else:
            raise

class DateRangeRetriever(BaseRetriever):
    vs: FAISS
    start_iso: Optional[str]
    end_iso: Optional[str]
    k: int
    fetch_k: int
    dedupe: bool = True

    class Config:
        arbitrary_types_allowed = True

    def get_relevant_documents(self, query: str) -> List[Document]:
        # 1) Over-fetch
        candidates = self.vs.similarity_search(query, k=self.fetch_k)

        # 2) Apply start_date filter, but keep chunks with no effective_date
        if self.start_iso:
            filtered = []
            for d in candidates:
                ed = d.metadata.get("effective_date")
                # include if no date OR date >= cutoff
                if ed is None or (isinstance(ed, str) and ed >= self.start_iso):
                    filtered.append(d)
            candidates = filtered

        # 3) Apply end_date filter, but keep chunks with no effective_date
        if self.end_iso:
            filtered = []
            for d in candidates:
                ed = d.metadata.get("effective_date")
                # include if no date OR date <= cutoff
                if ed is None or (isinstance(ed, str) and ed <= self.end_iso):
                    filtered.append(d)
            candidates = filtered

        # 4) Dedupe by raw_id if requested
        if self.dedupe:
            seen, unique = set(), []
            for d in candidates:
                rid = d.metadata.get("raw_id")
                if rid not in seen:
                    unique.append(d)
                    seen.add(rid)
                if len(unique) >= self.k:
                    break
            candidates = unique

        # 5) Truncate to k
        return candidates[: self.k]

def get_retriever(
    niche:       str,
    country:     str,
    k:           int = 8,
    *,
    recency_days: Optional[int] = 365,
    dedupe:      bool            = True,
    start_date:  Optional[str]   = None,
    end_date:    Optional[str]   = None
) -> BaseRetriever:
    vs = _load_vectorstore(niche, country)

    # derive lower‐bound date
    start_iso = start_date
    if not start_iso and recency_days and recency_days > 0:
        start_iso = (date.today() - timedelta(days=recency_days)).isoformat()

    fetch_k = k * 3
    return DateRangeRetriever(
        vs=vs,
        start_iso=start_iso,
        end_iso=end_date,
        k=k,
        fetch_k=fetch_k,
        dedupe=dedupe
    )
