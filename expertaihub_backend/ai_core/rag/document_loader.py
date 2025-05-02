import os
import sys
import django

# Add root folder to sys.path manually
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Manually configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'expertaihub_backend.settings')
django.setup()

# Now normal imports
from langchain_community.document_loaders import DirectoryLoader, UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from django.conf import settings
from dotenv import load_dotenv
load_dotenv()
# --- Your BASE_DIR and other code ---
BASE_DOCUMENTS_FOLDER = os.path.join(settings.BASE_DIR, "ai_core", "documents")
BASE_VECTORSTORE_FOLDER = os.path.join(settings.BASE_DIR, "ai_core", "rag", "vectorstores")

def load_and_embed_documents(niche: str, country_code: str):
    """
    Load documents, split them, create embeddings, and save FAISS vectorstore.
    """
    try:
        niche = niche.lower()
        country_code = country_code.lower()

        docs_path = os.path.join(BASE_DOCUMENTS_FOLDER, f"{niche}_docs", country_code)
        vector_path = os.path.join(BASE_VECTORSTORE_FOLDER, niche, country_code)

        if not os.path.exists(docs_path):
            raise FileNotFoundError(f"No documents directory found at {docs_path}")
        
        if not os.listdir(docs_path):
            raise ValueError(f"Directory {docs_path} exists but is empty")

        loader = DirectoryLoader(docs_path, glob="**/*.pdf", loader_cls=UnstructuredPDFLoader)
        raw_docs = loader.load()

        if not raw_docs:
            raise ValueError(f"No PDF documents found in {docs_path}")
        
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_docs = splitter.split_documents(raw_docs)
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        vectorstore = FAISS.from_documents(split_docs, embeddings)

        os.makedirs(vector_path, exist_ok=True)
        vectorstore.save_local(vector_path)

        print(f"✅ {len(split_docs)} chunks embedded for {niche.upper()} - {country_code.upper()} at '{vector_path}'")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise

load_and_embed_documents("immigration", "usa")

