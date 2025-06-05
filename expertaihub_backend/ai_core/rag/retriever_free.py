
import os
from django.conf import settings
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

BASE_VECTORSTORE_FOLDER = os.path.join(
    settings.BASE_DIR, "ai_core", "rag", "vectorstores", "free"
)

PHONE_CODE_TO_ISO = {
    "+1":    "usa",
    "+91":   "india",
    "+44":   "uk",
    "+61":   "australia",
    # ...
}

def get_retriever(niche: str, country_code, k: int = 8):
    niche = str(niche).lower()
    country = PHONE_CODE_TO_ISO.get(country_code, country_code.lower())
    vector_path = os.path.join(BASE_VECTORSTORE_FOLDER, niche, country)
    if not os.path.isdir(vector_path):
        raise FileNotFoundError(f"No vectorstore at '{vector_path}'")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )
    vectorstore = FAISS.load_local(
        vector_path,
        embeddings,
        allow_dangerous_deserialization=True
    )
    return vectorstore.as_retriever(search_kwargs={"k": k})