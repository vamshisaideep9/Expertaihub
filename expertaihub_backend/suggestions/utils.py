from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


INDEX_DIR = Path(__file__).resolve().parent / "vectorstores" / "free"

_embedder = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
)


def _load_index():
    if not (INDEX_DIR / "index.faiss").exists():
        return None
    return FAISS.load_local(
        str(INDEX_DIR),
        _embedder,
        allow_dangerous_deserialization=True,
    )


def top5_related(query_text):
    """Return up to five FAQ question texts closest to query_text."""
    index = _load_index()
    if not index:
        return []
    docs = index.similarity_search(query_text, k=5)
    return [d.page_content for d in docs]
