import logging
from types import GeneratorType
from typing import Any, Dict
import re
from ai_core.llm.llm_client_free import ask_openai
from ai_core.llm.llm_client_free import client
from ai_core.rag.retriever_free import get_retriever
from ai_core.prompts.prompts import (
    rephrase_prompt,
    intent_prompt,
    generate_response_prompt_free,
    safety_prompt,
)
from ai_core.langgraph.memory import MemoryStore
from langchain_core.memory import BaseMemory
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

VALID_INTENTS = {
    "greeting", "ask_form_info", "generate_form",
    "state_law_query", "followup", "unclear", "not_in_docs"
}


GENERATE_FORM_RE = re.compile(r"\b(generate|draft|pre-?fill|pre ?filled)\b", re.IGNORECASE)

GREETING_RE = re.compile(
    r"^\s*(?:hi|hii|hiii|hello|hey|hola|greetings|good\s+(?:morning|afternoon|evening))\b",
    re.IGNORECASE
)

# ─── Memory Hooks ────────────────────────────────────────────────────────────

def load_memory_node(state: Dict[str, Any]) -> Dict[str, Any]:
    mem = MemoryStore.load_for(state["session_id"])
    state["memory"] = mem
    return state

def add_user_message_node(state: Dict[str, Any]) -> Dict[str, Any]:
    state["memory"].chat_memory.add_user_message(state["question"])
    return state

def add_ai_message_node(state: Dict[str, Any]) -> Dict[str, Any]:
    state["memory"].chat_memory.add_ai_message(state["answer"])
    return state

def save_memory_node(state: Dict[str, Any]) -> Dict[str, Any]:
    MemoryStore.save_for(state["session_id"], state["memory"])
    return state

# ─── NLP Nodes ───────────────────────────────────────────────────────────────

def rephrase_input(state: Dict[str, Any]) -> Dict[str, Any]:
    raw = state["question"].strip()
    # Skip rephrase for very short or greeting inputs
    if len(raw.split()) < 3 or GREETING_RE.match(raw):
        state["clean_question"] = raw
        return state

    history = "\n".join(
        f"{'User' if isinstance(m,HumanMessage) else 'AI'}: {m.content}"
        for m in state["memory"].chat_memory.messages
    )
    prompt_str = rephrase_prompt.format(history=history, question=raw)
    out = ask_openai(prompt_str, stream=False)
    state["clean_question"] = out if isinstance(out, str) else "".join(out)
    logger.info(f"[rephrase_input] → {state['clean_question']!r}")
    return state



def detect_intent(state: Dict[str, Any]) -> Dict[str, Any]:
    raw_q = state["question"].strip()
    clean_q = state.get("clean_question", raw_q).strip()

    # 1) Greeting on raw input
    if GREETING_RE.match(raw_q):
        state["intent"] = "greeting"
        return state

    # 2) Generate form shortcut
    if GENERATE_FORM_RE.search(raw_q):
        state["intent"] = "generate_form"
        return state

    # 3) If the current question is < 5 words AND memory has valid immigration turns → followup
    if len(raw_q.split()) < 5:
        prev_msgs = state["memory"].chat_memory.messages[-3:]  # check last 3 turns
        if any("F-1" in m.content or "visa" in m.content or "Form AR-11" in m.content for m in prev_msgs):
            state["intent"] = "followup"
            return state

    # 4) Else → Use LLM prompt to classify
    history = "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'AI'}: {m.content}"
        for m in state["memory"].chat_memory.messages
    )

    prompt_str = intent_prompt.format(history=history, question=clean_q)
    out = ask_openai(prompt_str, stream=False)
    intent = out.strip().lower() if isinstance(out, str) else "".join(out).strip()
    state["intent"] = intent if intent in VALID_INTENTS else "unclear"
    return state


RISKY_PATTERN = re.compile(r"\b(overstay|expired visa|illegal|fake marriage|stay.*after.*visa|falsify|unlawful)\b", re.IGNORECASE)

def safety_guard(state: dict) -> dict:
    # 1) Short-circuit greetings
    if state.get("intent") == "greeting":
        state["is_safe"] = True
        return state

    # 2) Regex override for risky keywords
    question_text = state.get("clean_question", state.get("question", ""))
    if RISKY_PATTERN.search(question_text):
        logger.warning("[safety_guard] Triggered by regex unsafe phrase.")
        state["is_safe"] = False
        return state

    # 3) OpenAI Moderation fallback
    try:
        resp = client.moderations.create(
            model="omni-moderation-latest",
            input=question_text
        )
        state["is_safe"] = not resp.results[0].flagged
    except Exception as e:
        logger.error(f"[safety_guard] moderation error: {e}")
        state["is_safe"] = False
    return state

def retrieve_context(state: Dict[str, Any]) -> Dict[str, Any]:
    state["used_retrieval"] = True
    query = state.get("clean_question", state.get("question", "")).strip()
    
    # Step 1: Load from FAISS
    docs = get_retriever(
        state.get("niche", "immigration"),
        state.get("country", "usa"),
        k=4
    ).invoke(query)

    # Step 2: Filter out empty chunks
    filtered = [d.page_content.strip() for d in docs if d.page_content.strip()]
    state["docs"] = filtered

    # Step 3: Extract important words from the question
    stopwords = {"what", "in", "on", "at", "the", "a", "an", "for", "to", "of", "if", "about", "how", "do", "i"}
    keywords = [word for word in re.findall(r"\b\w+\b", query.lower()) if word not in stopwords]

    # Step 4: Check for relevance in any retrieved doc
    found = any(any(kw in doc.lower() for kw in keywords) for doc in filtered)

    if not found:
        # Manually force fallback node
        state["docs"] = []
        state["used_retrieval"] = False
        logger.warning(f"[retrieve_context] No relevant keywords from question found in docs → triggering denial")
    else:
        logger.info(f"[retrieve_context] Matched keywords in retrieved docs")

    return state

def generate_response(state: Dict[str, Any]) -> Dict[str, Any]:
    docs = state.get("docs", [])
    if not docs:
        state["answer"] = "Sorry, I couldn’t find relevant info. Please check USCIS.gov."
        return state
    history = "\n".join(
        f"{'User' if isinstance(m,HumanMessage) else 'AI'}: {m.content}"
        for m in state["memory"].chat_memory.messages
    )
    prompt_str = generate_response_prompt_free.format(
        history=history,
        context="\n\n".join(docs),
        question=state["question"],
        country=state.get("country","").upper(),
        niche=state.get("niche",""),
        form_name=state.get("form_name","")
    )
    state["answer"] = prompt_str
    logger.info(f"[generate_response] prompt_len={len(prompt_str)}")
    return state

def generate_document(state: Dict[str, Any]) -> Dict[str, Any]:
    q = (state.get("clean_question") or "").lower()
    if "ar-11" in q or "address change" in q:
        state["answer"] = "Form-drafting is a Pro+ feature. Upgrade to Pro for pre-filled forms."
    else:
        state["answer"] = "Document generation coming soon."
    return state

def clarify_question(state: Dict[str, Any]) -> Dict[str, Any]:
    state["answer"] = "Could you please clarify what you mean?"
    return state

def greet_user(state: Dict[str, Any]) -> Dict[str, Any]:
    state["answer"] = "👋 Hello! How can I help you with your immigration question today?"
    return state

def deny_answer_confidently(state: Dict[str, Any]) -> Dict[str, Any]:
    state["answer"] = "I’m sorry, I can’t help you with that."
    return state

def log_query(state: Dict[str, Any]) -> Dict[str, Any]:
    # e.g. analytics or DB writes
    return state



# ai_core/langgraph/nodes/summary_nodes.py

import logging
import tiktoken
from ai_core.llm.llm_client_free import ask_openai
from typing import Dict, List

logger = logging.getLogger(__name__)

# Be more aggressive:
MAX_CONTEXT_TOKENS = 2000
SUMMARY_TARGET_TOKENS = 300

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    except Exception:
        return len(text.split())

def summarize_context(state: Dict) -> Dict:
    """
    Keep the first 2 chunks raw. Always summarize chunks 3 and 4 if they exist.
    If there are exactly 3 or 4 total, we bundle chunk #3 onward into one ~300-token summary.
    """
    raw_docs: List[str] = state.get("docs", [])
    if not raw_docs:
        state["trimmed_docs"] = []
        return state

    # 1) Always keep _at most_ the first 2 raw chunks
    kept = raw_docs[:2]
    logger.debug(f"[summarize_context] initial kept={len(kept)} chunks")

    # 2) Everything else (chunks #3 and #4) goes into a summary, if present
    overflow_for_summary = raw_docs[2:]  # this can have length 0,1,2

    summary_text = ""
    if overflow_for_summary:
        # Join overflow chunks with separators so the LLM sees them distinctly
        remainder = "\n\n---\n\n".join(overflow_for_summary)
        summary_prompt = (
            "You are a concise U.S. immigration assistant. Summarize the following excerpts into "
            f"around {SUMMARY_TARGET_TOKENS} tokens, focusing on key steps, deadlines, and compliance notes:\n\n"
            f"{remainder}\n\n**Summary:**"
        )

        try:
            resp = ask_openai(summary_prompt, max_tokens=SUMMARY_TARGET_TOKENS, stream=False)
            summary_text = resp.strip() if isinstance(resp, str) else "".join(resp).strip()
        except Exception as e:
            logger.error(f"[summarize_context] LLM summarization failed: {e}", exc_info=True)
            # If summarization fails, just keep the first overflow chunk raw
            summary_text = overflow_for_summary[0]

    # 3) Build final trimmed_docs: the 2 raw chunks + the summary (if any)
    trimmed = kept.copy()
    if summary_text:
        trimmed.append(summary_text)

    state["trimmed_docs"] = trimmed
    logger.info(
        f"[summarize_context] kept={len(kept)} raw chunks, "
        f"summary_included={'yes' if summary_text else 'no'}"
    )
    return state