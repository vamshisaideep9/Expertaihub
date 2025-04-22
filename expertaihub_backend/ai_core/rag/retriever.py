import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings



def get_retriever(niche: str, country_code: str, k: int = 4):
    """
    Load a retriever for the given niche and country.
    Returns a retriever ready for use in LangGraph or QA Chains.
    """

    try:
        niche = niche.lower()
        country_code = country_code.lower()

        vector_path = f"c:/Users/vamsh/OneDrive/Desktop/ExpertAiHub/Expertaihub/expertaihub_backend/ai_core/rag/vectorstores/{niche}/{country_code}"

        if not os.path.exists(vector_path):
            raise FileNotFoundError(f"❌ No vectorstore found at {vector_path}")
        
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.load_local(vector_path, embeddings, allow_dangerous_deserialization=True)

        return vectorstore.as_retriever(search_kwargs={"k": k})
    except Exception as e:
        print(f"Error loading retriever: {str(e)}")
        raise


