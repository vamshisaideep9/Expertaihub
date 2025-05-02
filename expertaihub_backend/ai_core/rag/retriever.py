import os
from django.conf import settings
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

BASE_VECTORSTORE_FOLDER = os.path.join(
    settings.BASE_DIR, "ai_core", "rag", "vectorstores"
)

def get_retriever(niche: str, country_code: str, k: int = 4):
    niche = niche.lower()
    country = country_code.lower()
    vector_path = os.path.join(BASE_VECTORSTORE_FOLDER, niche, country)

    if not os.path.isdir(vector_path):
        raise FileNotFoundError(f"No vectorstore found at '{vector_path}'")

    # Load embeddings (all-local, free)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    # Load FAISS index
    vectorstore = FAISS.load_local(
        vector_path,
        embeddings,
        allow_dangerous_deserialization=True
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    print(f"✅ Retriever loaded: {niche.upper()} – {country.upper()} (k={k})")
    return retriever
