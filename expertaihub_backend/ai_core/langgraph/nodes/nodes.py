import re
from ai_core.llm.llm_client import ask_together
from ai_core.rag.retriever import get_retriever
from ai_core.prompts.prompts import (
    rephrase_prompt,
    intent_prompt,
    generate_response_prompt,
    safety_prompt,
    fallback_prompt
)
from langchain_core.messages import HumanMessage




def rephrase_input(state:dict) -> dict:
    question = state["question"]
    history = ""
    mem = state.get("memory")
    if mem:
        for msg in mem.chat_memory.messages:
            role = "User" if isinstance(msg, HumanMessage) else "AI"
            history += f"{role}: {msg.content}\n"
    prompt = rephrase_prompt.format(question=question, history=history.strip())
    state["clean_question"] = ask_together(prompt)
    return state


GREETING_RE = re.compile(r"""
    ^\s*
    (?:
      good\ (?:morning|afternoon|evening) |
      hi(?:\s+there)? |
      hello(?:\s+there)? |
      hey(?:\s+there)? |
      hola |
      greetings |
      what(?:'s| is)\ up
    )
    [\W_]*$
""", re.IGNORECASE | re.VERBOSE)


def detect_intent(state: dict) -> dict:
    q = state["clean_question"].strip()

    if GREETING_RE.match(q):
        state["intent"] = "greeting"
        return state
    
    history = ""
    mem = state.get("memory")
    if mem:
        for msg in mem.chat_memory.messages:
            role = "User" if isinstance(msg, HumanMessage) else "AI"
            history += f"{role}: {msg.content}\n"

    prompt = intent_prompt.format(question=q, history=history.strip())
    intent = ask_together(prompt).strip().lower()

    valid = {
        "greeting", "ask_form_info", "generate_form",
        "state_law_query", "followup", "unclear", "not_in_docs"
    }
    state["intent"] = intent if intent in valid else "unclear"
    return state


def safety_guard(state: dict) -> dict:
    q = state["clean_question"]
    prompt = safety_prompt(q)
    decision = ask_together(prompt).lower()
    state["is_safe"] = (decision == "safe")
    return state



def retrieve_context(state: dict) -> dict:
    """
    Free tier: always k=2 and mark that we did a retrieval.
    """
    # 1) mark that we performed a RAG lookup
    state["used_retrieval"] = True

    # 2) actually pull the docs
    docs = get_retriever(
        state.get("niche", "immigration"),
        state.get("country", "usa"),
        k=3
    ).invoke(state["clean_question"])

    state["docs"] = [d.page_content for d in docs]
    return state



def generate_response(state: dict) -> dict:
    q = state["clean_question"]
    docs = state.get("docs", [])
    if not docs:
        return {"answer": "Sorry, I couldn’t find relevant info. Please check USCIS.gov."}

    history = ""
    mem = state.get("memory")
    if mem:
        for msg in mem.chat_memory.messages:
            role = "User" if isinstance(msg, HumanMessage) else "AI"
            history += f"{role}: {msg.content}\n"

    prompt = generate_response_prompt.format(
        question=q,
        context="\n\n".join(docs)[:100000],
        history=history.strip()
    )
    ans = ask_together(prompt)
    # store in convo memory
    if mem:
        mem.chat_memory.add_user_message(q)
        mem.chat_memory.add_ai_message(ans)
    return {"answer": ans}


def generate_document(state: dict) -> dict:
    q = state["clean_question"].lower()
    if "ar-11" in q or "address change" in q:
        return {
            "answer": (
                "Form‐drafting is a Pro+ feature. "
                "Upgrade to Pro to get step-by-step draft guides and pre-filled forms."
            )
        }
    return {"answer": "Document generation coming soon."}


def clarify_question(state: dict) -> dict:
    return {"answer": "Could you please clarify what you mean?"}


def greet_user(state: dict) -> dict:
    return {"answer": "👋 Hello! How can I help you with your immigration question today?"}


def deny_answer_confidently(state: dict) -> dict:
    return {
        "answer": (
            "I’m sorry, I can’t help with that. "
            "Please refer to official sources like USCIS.gov."
        )
    }


def safe_guidance_for_risky_cases(state: dict) -> dict:
    prompt = fallback_prompt(state["clean_question"])
    ans = ask_together(prompt)
    return {"answer": ans}


def log_query(state: dict) -> dict:
    # you could write to a DB or analytics here
    return state

# def apply_subscription(state:dict) -> dict:
#     """
#     Read state['subscription_tier'] ("free"|"pro"|"premium")
#     and sets retrieval depth & form-generation flags.
#     """

#     tier = state.get("subscription_tier", "free").lower()

#     if tier == "pro":
#         state["retrieval_k"] = 4
#         state["allow_draft"] = True
#         state["allow_full_form"] = False
#     elif tier == "premium":
#         state["retrieval_k"]     = 8
#         state["allow_draft"]     = True
#         state["allow_full_form"] = True
#     else: #Free
#         state["retrieval_k"]     = 2
#         state["allow_draft"]     = False
#         state["allow_full_form"] = False
#     return state