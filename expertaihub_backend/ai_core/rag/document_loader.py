import os
from langchain_community.document_loaders import DirectoryLoader, UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
load_dotenv()


LANGSMITH_TRACKING = os.getenv("LANGSMITH_TRACKING")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT_NAME = os.getenv("LANGSMITH_PROJECT_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")




def load_and_embed_documents(niche: str, country_code: str):
    """
    Load docs and build vectorstore for a specific niche + country.
    """
    try:
        niche = niche.lower()
        country_code = country_code.lower()

        docs_path = f"c:/Users/vamsh/OneDrive/Desktop/ExpertAiHub/Expertaihub/expertaihub_backend/ai_core/documents/{niche}_docs/{country_code}"
        vector_path = f"c:/Users/vamsh/OneDrive/Desktop/ExpertAiHub/Expertaihub/expertaihub_backend/ai_core/rag/vectorstores/{niche}/{country_code}"

        print(f"Looking for documents in: {docs_path}")  # Debug print

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

        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(split_docs, embeddings)

        os.makedirs(vector_path, exist_ok=True)
        vectorstore.save_local(vector_path)

        print(f"✅ {len(split_docs)} chunks embedded for {niche.upper()} - {country_code} at '{vector_path}'")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        raise


load_and_embed_documents("immigration", "usa")

