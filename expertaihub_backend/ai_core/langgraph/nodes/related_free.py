import logging
from typing import Any, Dict, List

from langchain_core.runnables import Runnable

from ai_core.llm.llm_client_free import ask_openai
from suggestions.utils import top5_related
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

# Use the same model as the FAQ vector store
EMBEDDER = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
)

SMALL_PROMPT = (
    "Suggest 3-5 short follow-up U.S. immigration questions someone might ask "
    "after: {question}\n\nReturn each on its own line."
)

class RelatedFree(Runnable):
    """Return up to five related questions for a chat answer."""

    def invoke(self, state: Dict[str, Any], config: Dict | None = None) -> Dict[str, Any]:
        question = state.get("question") or state.get("user_question", "")

        # Compute embedding (same model as vector store)
        try:
            _ = EMBEDDER.embed_query(question)
        except Exception as e:
            logger.warning("[RelatedFree] embedding failed: %s", e)

        suggestions: List[str] = top5_related(question)

        if not suggestions:
            try:
                resp = ask_openai(SMALL_PROMPT.format(question=question), stream=False)
                text = resp if isinstance(resp, str) else "".join(resp)
                suggestions = [s.strip("-•* ").strip() for s in text.splitlines() if s.strip()]
            except Exception as e:
                logger.error("[RelatedFree] Fallback prompt failed: %s", e, exc_info=True)
                suggestions = []

        state["related_queries"] = suggestions
        return state
