#nodes/nodes.py

import logging
from types import GeneratorType
from typing import Any, Dict, List
import re
from datetime import date
from dateparser.search import search_dates

from ai_core.llm.llm_client_free import ask_openai, client, DEFAULT_REASONING_EFFORT
from ai_core.rag.retriever_free import get_retriever
from ai_core.rag.retriever_plus import get_retriever_openai
from ai_core.prompts.prompts import (
    rephrase_prompt,
    intent_prompt,
    generate_response_prompt,
    safety_prompt,
)
from ai_core.langgraph.memory import MemoryStore
from langchain_core.memory import BaseMemory
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS AND REGEX PATTERNS
# =============================================================================

VALID_INTENTS = {
    "greeting", "ask_form_info", "generate_form",
    "state_law_query", "followup", "simple_info", "summary",
    "unclear", "not_in_docs", "ask_forecast"
}

# Intent detection patterns
GENERATE_FORM_RE = re.compile(r"\b(generate|draft|pre-?fill|pre ?filled)\b", re.IGNORECASE)
GREETING_RE = re.compile(
    r"^\s*(?:hi|hii|hiii|hello|hey|hola|greetings|good\s+(?:morning|afternoon|evening))\b",
    re.IGNORECASE
)

SUMMARY_RE = re.compile(r"\b(summariz|brief|overview)\b", re.IGNORECASE)
# Date parsing patterns
BEFORE_RE = re.compile(r"\b(before|prior to|until)\b", re.IGNORECASE)
AFTER_RE = re.compile(r"\b(since|after|from)\b", re.IGNORECASE)
PAST_DATA_RE = re.compile(r"\b(past|historical|history|previous|before)\b", re.IGNORECASE)

# Year range patterns
YEAR_RANGE_RE = re.compile(r"\bfrom\s+(\d{4})\s*(?:to|[-–—])\s*(\d{4})\b", re.IGNORECASE)
SIMPLE_YEAR_RANGE_RE = re.compile(r"\b(\d{4})\s*[-–—]\s*(\d{4})\b")

# Safety patterns
RISKY_PATTERN = re.compile(r"\b(overstay|expired visa|illegal|fake marriage|stay.*after.*visa|falsify|unlawful)\b", re.IGNORECASE)

FORECAST_RE = re.compile(r"\b(forecast|predict|projection|FY\s*2026)\b", re.IGNORECASE)

# =============================================================================
# DATE PARSING FUNCTIONS
# =============================================================================

def parse_date_filter(state: Dict[str, Any]) -> Dict[str, Any]:
    """Parse date filters from the question and update state accordingly."""
    q = state.get("question", "")
    
    # 1) Year–Year or "from YYYY to YYYY"
    m = YEAR_RANGE_RE.search(q) or SIMPLE_YEAR_RANGE_RE.search(q)
    if m:
        y1, y2 = int(m.group(1)), int(m.group(2))
        start, end = min(y1, y2), max(y1, y2)
        state["start_date"] = f"{start:04d}-01-01"
        state["end_date"] = f"{end:04d}-12-31"
        return state

    # 2) Full-date parsing
    results = search_dates(q, settings={
        "PREFER_DAY_OF_MONTH": "first", "STRICT_PARSING": True
    }) or []
    dates = sorted({dt.date() for _, dt in results})
    if not dates:
        return state

    iso = dates[0].isoformat()
    if BEFORE_RE.search(q):
        state["end_date"] = iso
    elif AFTER_RE.search(q):
        state["start_date"] = iso
    else:
        # default to "since"
        state["start_date"] = iso

    return state

# =============================================================================
# MEMORY MANAGEMENT FUNCTIONS
# =============================================================================

def load_memory_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Load memory for the current session."""
    mem = MemoryStore.load_for(state["session_id"])
    state["memory"] = mem
    return state

def add_user_message_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Add user message to chat memory."""
    state["memory"].chat_memory.add_user_message(state["question"])
    return state

def add_ai_message_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Add AI message to chat memory."""
    state["memory"].chat_memory.add_ai_message(state["answer"])
    return state

def save_memory_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Save memory for the current session."""
    MemoryStore.save_for(state["session_id"], state["memory"])
    return state

# =============================================================================
# NLP PROCESSING FUNCTIONS
# =============================================================================

def rephrase_input(state: Dict[str, Any]) -> Dict[str, Any]:
    """Rephrase user input for better processing."""
    raw = state["question"].strip()
    # Skip rephrase for very short or greeting inputs
    if len(raw.split()) < 3 or GREETING_RE.match(raw):
        state["clean_question"] = raw
        return state

    history = "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'AI'}: {m.content}"
        for m in state["memory"].chat_memory.messages
    )
    prompt_str = rephrase_prompt.format(history=history, question=raw)
    out = ask_openai(prompt_str, stream=False)
    state["clean_question"] = out if isinstance(out, str) else "".join(out)
    logger.info(f"[rephrase_input] → {state['clean_question']!r}")
    return state

def detect_intent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Detect the intent of the user's question."""
    raw_q = state["question"].strip()
    logger.debug(f"[detect_intent] raw question: {raw_q!r}")
    clean_q = state.get("clean_question", raw_q).strip()
    logger.debug(f"[detect_intent] clean question: {clean_q!r}")
    mem = MemoryStore.load_for(state["session_id"])

    # ─── date overrides ──────────────────────────────────────────────────────
    # 1) historical/past override → no recency cutoff
    if PAST_DATA_RE.search(raw_q):
        state["recency_days"] = None
    else:
        state.setdefault("recency_days", 365)

    # 2) year-only range override → explicit start_date/end_date
    m = YEAR_RANGE_RE.search(raw_q) or SIMPLE_YEAR_RANGE_RE.search(raw_q)
    if m:
        y1, y2 = int(m.group(1)), int(m.group(2))
        start, end = min(y1, y2), max(y1, y2)
        state["start_date"] = f"{start:04d}-01-01"
        state["end_date"] = f"{end:04d}-12-31"
    # ─────────────────────────────────────────────────────────────────────────

    # 3) Greeting shortcut
    if GREETING_RE.match(raw_q):
        state["intent"] = "greeting"
        return state

    # 4) Generate-form shortcut
    if GENERATE_FORM_RE.search(raw_q):
        state["intent"] = "generate_form"
        return state
    
    if SUMMARY_RE.search(raw_q):
        state["intent"] = "summary"
        return state
    
    if FORECAST_RE.search(clean_q):
        logger.info("[detect_intent] Forecast trigger matched")
        state["intent"] = "ask_forecast"
        return state
    
    if re.search(r"\b(fee|cost|price|charge)\b", raw_q, re.IGNORECASE):
        state["intent"] = "simple_info"
        return state

    # 5) Very short follow-up
    if len(raw_q.split()) < 5:
        last_msgs = mem.chat_memory.messages[-3:]
        if any("visa" in m.content.lower() or "form ar-11" in m.content.lower()
               for m in last_msgs):
            state["intent"] = "followup"
            return state

    # 6) LLM classification fallback
    history = "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'AI'}: {m.content}"
        for m in mem.chat_memory.messages
    )
    prompt_str = intent_prompt.format(history=history, question=clean_q)
    out = ask_openai(prompt_str, stream=False)
    logger.debug(f"[detect_intent] intent LLM output: {out!r}")
    intent = (out.strip().lower() if isinstance(out, str)
              else "".join(out).strip().lower())
    logger.info(f"[detect_intent] resolved intent: {intent}")
    state["intent"] = intent if intent in VALID_INTENTS else "unclear"
    return state

def safety_guard(state: dict) -> dict:
    """Check if the question is safe to answer."""
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

# =============================================================================
# CONTEXT RETRIEVAL AND PROCESSING
# =============================================================================

def retrieve_context(state: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve relevant context documents for the question."""
    # 0) Apply any explicit date filters (year ranges, since/until, etc.)
    state = parse_date_filter(state)

    state["used_retrieval"] = True
    query = state.get("clean_question", state.get("question", "")).strip()

    # 1) Pull retrieval params out of state
    index = state.get("retriever_index")
    niche = state.get("niche", "immigration")
    country = state.get("country", "usa")
    if index:
        pieces = index.split("_")
    # 2) drop tier suffix if present
        if pieces[-1] in {"plus", "proplus"}:
            pieces = pieces[:-1]                # strip suffix
    # 3) expect <niche>_<country>
        if len(pieces) >= 2:
            niche, country = pieces[0], "_".join(pieces[1:])
    k = int(state.get("max_docs", 8))
    recency_days = state.get("recency_days", None)  # None → no cutoff
    start_date = state.get("start_date", None)   # ISO str or None
    end_date = state.get("end_date", None)     # ISO str or None

    # 2) Instantiate the retriever with date windows & dedupe
    tier = (state.get("tier") or "free").lower()
    if tier == "free":
        retriever = get_retriever(
            niche,
            country,
            k=k,
            recency_days=recency_days,
            dedupe=True,
            start_date=start_date,
            end_date=end_date,
        )
    else:
        retriever = get_retriever_openai(
            niche,
            country,
            k=k,
            recency_days=recency_days,
            dedupe=True,
            start_date=start_date,
            end_date=end_date,
        )

    # 3) Fetch the top-k chunks
    try:
        docs = retriever.invoke(query)
    except Exception as e:
        logger.error(f"[retrieve_context] retrieval error: {e}")
        state["docs"] = []
        return state

    # 4) Strip out empty text
    state['docs'] = [d.page_content.strip() for d in docs if d.page_content.strip()]

    state["used_retrieval"] = bool(state["docs"])
    if not state["docs"]:
            logger.warning("[retrieve_context] no documents returned from RAG")

    return state

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count tokens in text using tiktoken."""
    try:
        import tiktoken
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
            f"around 500 tokens, focusing on key steps, deadlines, and compliance notes:\n\n"
            f"{remainder}\n\n**Summary:**"
        )

        try:
            resp = ask_openai(summary_prompt, max_tokens=500, stream=False)
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

# =============================================================================
# RESPONSE GENERATION FUNCTIONS
# =============================================================================

def generate_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a response based on retrieved context."""
    # 1) Pick the best context: trimmed if available, else full docs
    docs: List[str] = state.get("trimmed_docs") or state.get("docs", [])
    if not docs:
        logger.warning("[generate_response] No context documents available")
        state["answer"] = ""
        return state

    # 2) Build chat history
    mem = MemoryStore.load_for(state["session_id"])
    history = "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'AI'}: {m.content}"
        for m in mem.chat_memory.messages
    )

    # 3) Build the prompt
    prompt = generate_response_prompt.format(
        history=history,
        context="\n\n".join(docs),
        question=state["question"],
        form_name=state.get("form_name", "")
    )
    logger.debug(f"[generate_response] Prompt length={len(prompt)}; docs_count={len(docs)}")

    try:
        # 4) Call the LLM
        completion = ask_openai(prompt, stream=False)
        if isinstance(completion, str):
            answer_body = completion.strip()
        elif isinstance(completion, (list, GeneratorType)):
            answer_body = "".join(completion).strip()
        else:
            logger.error(f"[generate_response] Unexpected completion type: {type(completion)}")
            answer_body = "I'm sorry, I couldn't generate a proper answer right now."

        if not answer_body:
            raise ValueError("Received empty answer from LLM")

    except Exception as e:
        logger.error(f"[generate_response] LLM error: {e}", exc_info=True)
        answer_body = "I'm sorry, I encountered an error while generating the answer. Please try again."
    full_answer = f"{answer_body}"

    state["answer"] = full_answer
    logger.info(f"[generate_response] Answer length={len(full_answer)} chars")
    return state

def generate_document(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a document based on the request."""
    q = (state.get("clean_question") or "").lower()
    if "ar-11" in q or "address change" in q:
        state["answer"] = "Form-drafting is a Pro+ feature. Upgrade to Pro for pre-filled forms."
    else:
        state["answer"] = "Document generation coming soon."
    return state

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def clarify_question(state: Dict[str, Any]) -> Dict[str, Any]:
    """Ask for clarification when the question is unclear."""
    state["answer"] = "Could you please clarify what you mean?"
    return state


def generate_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """Very brief summary when user asks to summarize."""
    docs = state.get("docs", [])
    if not docs:
        state["answer"] = "Sorry, I don't have anything to summarize."
        return state

    # Join all docs into one blob for summary prompt
    blob = "\n\n---\n\n".join(docs)
    prompt = (
        "## Summary\n\n"
        "Please write a concise (2–4 sentence) summary of these excerpts:\n\n"
        f"{blob}"
    )
    try:
        resp = ask_openai(prompt, stream=False)
        summary = resp if isinstance(resp, str) else "".join(resp)
        state["answer"] = summary.strip()
    except Exception:
        state["answer"] = "Sorry, I couldn't generate a summary right now."
    return state

from datetime import date

def simple_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """Use the LLM to give a concise multi‐sentence answer for single‐item queries (fees, costs)."""
    question = state.get("question", "").strip()
    docs     = state.get("docs", [])

    # Build prompt: include up to 3 chunks if available, else fall back to direct
    if docs:
        context = "\n\n".join(docs[:3])
        prompt = (
            "You are a friendly U.S. immigration assistant.\n\n"
            f"Context:\n{context}\n\n"
            f"User question: \"{question}\"\n\n"
            "Based on the above, provide a concise 2–3 sentence answer "
            "specifically about the filing fee and any immediate payment instructions.\n\n"
            "Answer:"
        )
    else:
        today = date.today().isoformat()
        prompt = (
            "You are a knowledgeable U.S. immigration assistant.\n\n"
            f"As of {today}, what is the current filing fee for Form I-485 and how should it be paid? "
            "Answer in 2–3 sentences.\n\n"
            "Answer:"
        )

    try:
        resp   = ask_openai(prompt, stream=False)
        answer = resp if isinstance(resp, str) else "".join(resp)
        state["answer"] = answer.strip()
    except Exception as e:
        logger.error(f"[simple_response] LLM error: {e}", exc_info=True)
        state["answer"] = "Sorry, I couldn't retrieve the fee information at the moment."

    return state


def greet_user(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a greeting response."""
    raw = state.get("question", "").strip()
    # Build a mini prompt to steer the model toward a friendly greeting
    prompt = (
        "You are a friendly U.S. immigration virtual assistant. "
        "The user just said: \"{user_input}\". "
        "Reply with a brief, engaging greeting that confirms you're ready to help with their immigration question—no extra explanation.\n\n"
        "Assistant:"
    ).format(user_input=raw)

    try:
        # ask_openai returns either a string or list; coerce to string
        resp = ask_openai(prompt, stream=False)
        answer = resp if isinstance(resp, str) else "".join(resp)
        state["answer"] = answer.strip()
    except Exception as e:
        # Fallback to a safe default
        state["answer"] = "👋 Hello! How can I assist you with your immigration question today?"
    return state

def deny_answer_confidently(state: Dict[str, Any]) -> Dict[str, Any]:
    """Deny answering the question."""
    state["answer"] = "I'm sorry, I can't help you with that."
    return state

def log_query(state: Dict[str, Any]) -> Dict[str, Any]:
    """Log the query for analytics or database writes."""
    # e.g. analytics or DB writes
    return state