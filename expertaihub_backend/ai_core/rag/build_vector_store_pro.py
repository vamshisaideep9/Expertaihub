import os
from pathlib import Path
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "expertaihub_backend.settings")
django.setup()

from django.conf import settings
from ai_core.models import DocumentChunk
from langchain.schema import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

BASE_VS_PATH = Path(settings.BASE_DIR) / "ai_core" / "rag" / "vectorstores"

def build_vectorstore_pro(niche: str, country: str):
    chunks = DocumentChunk.objects.filter(
        metadata__niche=niche, metadata__country=country
    ).order_by("raw_document_id", "chunk_index")
    if not chunks:
        raise ValueError("No chunks for %s/%s" % (niche, country))

    docs = [
        Document(
            page_content=c.text,
            metadata={**c.metadata, "raw_id": c.raw_document_id, "chunk": c.chunk_index}
        )
        for c in chunks
    ]

    # high-quality embedder
    embedder = OpenAIEmbeddings(model="text-embedding-3-large")
    vs = FAISS.from_documents(docs, embedder)

    out = BASE_VS_PATH / "pro" / niche / country
    out.mkdir(parents=True, exist_ok=True)
    vs.save_local(str(out))
    print(f"✅ Pro vectorstore built: {out} ({len(docs)} docs)")

if __name__ == "__main__":
    build_vectorstore_pro("immigration", "usa")
