import os
import sys
import django
import logging
from pathlib import Path

PROJECT_ROOT = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "expertaihub_backend.settings")
django.setup()

from django.conf import settings
from ai_core.models import DocumentChunk
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


BASE_VECTORSTORE_FOLDER = Path(settings.BASE_DIR) / "ai_core" / "rag" / "vectorstores" / "free"

def build_vectorstore_from_db(niche: str, country: str, batch_size: int = 512):
    niche = niche.lower()
    country = country.lower()
    out_dir = BASE_VECTORSTORE_FOLDER / niche / country
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"📥 Fetching DocumentChunks for niche='{niche}', country='{country}'")
    chunks_qs = DocumentChunk.objects.filter(
        metadata__niche=niche,
        metadata__country=country,
    ).order_by("raw_document_id", "chunk_index")

    total_chunks = chunks_qs.count()
    if total_chunks == 0:
        logger.warning(f"❌ No chunks found for {niche}/{country}")
        return

    # Embed all chunks (or subset if tracked externally)
    logger.info(f"🔍 Preparing to embed {total_chunks} chunks")
    docs = []
    for chunk in chunks_qs:
        metadata = chunk.metadata.copy()
        metadata.update({
            "raw_id": chunk.raw_document_id,
            "chunk_index": chunk.chunk_index,
        })
        docs.append(Document(page_content=chunk.text, metadata=metadata))

    # Load embedder
    logger.info("🧠 Initializing HuggingFaceEmbeddings (all-MiniLM-L6-v2)")
    embedder = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        encode_kwargs={"batch_size": batch_size},
    )

    # Load existing or build new vectorstore
    if out_dir.exists() and any(out_dir.iterdir()):
        logger.info("🔄 Existing FAISS index found — loading and appending new vectors")
        vectorstore = FAISS.load_local(str(out_dir), embeddings=embedder, allow_dangerous_deserialization=True)
        new_vectorstore = FAISS.from_documents(docs, embedder)
        vectorstore.merge_from(new_vectorstore)
    else:
        logger.info("🆕 No FAISS index found — creating fresh one")
        vectorstore = FAISS.from_documents(docs, embedder)

    logger.info(f"💾 Saving updated FAISS index to {out_dir}")
    vectorstore.save_local(str(out_dir))
    logger.info(f"✅ Done: embedded and indexed {len(docs)} chunks for {niche}/{country}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python build_vectorstore_from_db.py <niche> <country_code>")
        sys.exit(1)
    build_vectorstore_from_db(sys.argv[1], sys.argv[2])
