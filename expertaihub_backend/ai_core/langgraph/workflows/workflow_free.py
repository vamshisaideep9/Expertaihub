# ai_core/langgraph/workflows/workflow_free.py
import re
from langgraph.graph import StateGraph
from langchain_core.memory import BaseMemory
from typing import TypedDict, Optional, List

from ai_core.langgraph.nodes.nodes import (
    rephrase_input,
    detect_intent,
    safety_guard,
    retrieve_context,
    generate_response,
    generate_document,
    clarify_question,
    greet_user,
    deny_answer_confidently,
    safe_guidance_for_risky_cases,
    log_query,
)



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

class GraphState(TypedDict):
    question:        str
    clean_question:  Optional[str]
    intent:          Optional[str]
    is_safe:         Optional[bool]
    docs:            Optional[List[str]]
    used_retrieval:  bool
    answer:          Optional[str]
    niche:           Optional[str]
    country:         Optional[str]
    memory:          Optional[BaseMemory]


def get_free_immigration_graph():
    g = StateGraph(GraphState)

    def detect_raw_greeting(state):
        q = state["question"].strip()
        if GREETING_RE.match(q):
            state["intent"] = "greeting"
            # skip rephrase & everything else
            state["skip_to"] = "greet_user"
        return state

    g.add_node("detect_raw_greeting", detect_raw_greeting)

    # 1) Declare all nodes
    g.add_node("rephrase_input",    rephrase_input)
    g.add_node("detect_intent",     detect_intent)
    g.add_node("safety_guard",      safety_guard)
    g.add_node("retrieve_context",  retrieve_context)
    g.add_node("generate_response", generate_response)
    g.add_node("generate_document", generate_document)
    g.add_node("clarify_question",  clarify_question)
    g.add_node("greet_user",        greet_user)
    g.add_node("deny_answer_confidently", deny_answer_confidently)
    g.add_node("safe_fallback",     safe_guidance_for_risky_cases)
    g.add_node("log_query",         log_query)

    # 2) Entry point
    g.set_entry_point("detect_raw_greeting")

    def route_after_greeting(state):
        return "greet_user" if state.get("skip_to") == "greet_user" else "rephrase_input"

    g.add_conditional_edges(
    "detect_raw_greeting",
    route_after_greeting,
    {
        "greet_user":     "greet_user",
        "rephrase_input": "rephrase_input",
    }
)

    # 3) Straight‐line flow
    g.add_edge("rephrase_input", "detect_intent")
    g.add_edge("detect_intent",    "safety_guard")

    # 4) Safety‐guard branch
    def is_safe(state): return state.get("is_safe", False)
    # a small “router” node to dispatch by intent
    g.add_node("router", lambda s: s)
    g.add_conditional_edges(
        "safety_guard",
        is_safe,
        {True: "router", False: "safe_fallback"}
    )

    # 5) Intent‐based routing
    def get_intent(state): return state.get("intent", "") or ""
    g.add_conditional_edges(
        "router",
        get_intent,
        {
            "greeting":        "greet_user",
            "ask_form_info":   "retrieve_context",
            "state_law_query": "retrieve_context",
            "followup":        "retrieve_context",
            "generate_form":   "generate_document",
            "unclear":         "clarify_question",
            "not_in_docs":     "deny_answer_confidently",
        }
    )
    # explicit fallback if no intent match
    g.add_edge("router", "deny_answer_confidently")

    # 6) RAG retrieval → response
    g.add_edge("retrieve_context", "generate_response")

    # 7) All terminal nodes chain into log_query
    for terminal in [
        "greet_user",
        "safe_fallback",
        "generate_document",
        "generate_response",
        "clarify_question",
        "deny_answer_confidently",
    ]:
        g.add_edge(terminal, "log_query")

    # 8) Finish at log_query
    g.set_finish_point("log_query")

    return g.compile()
