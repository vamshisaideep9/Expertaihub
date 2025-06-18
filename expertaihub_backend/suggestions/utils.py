from functools import lru_cache
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


# Default location for the FAQ vector store
INDEX_DIR = Path(__file__).resolve().parent / "vectorstores" / "free"


@lru_cache(maxsize=1)
def load_faq_vectorstore():
    """Load the FAQ FAISS vector store if present."""
    index_path = INDEX_DIR / "index.faiss"
    if not index_path.exists():
        return None

    embedder = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )
    return FAISS.load_local(
        str(INDEX_DIR), embedder, allow_dangerous_deserialization=True
    )


def top5_related(question_text: str):
    """Return up to five FAQ question texts closest to ``question_text``."""
    vs = load_faq_vectorstore()
    if not vs:
        return []

    docs = vs.similarity_search(question_text, k=5)
    return [d.page_content for d in docs]
