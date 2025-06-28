# ai_core/langgraph/graphs.py

from typing import Optional, List, TypedDict, Literal
from langgraph.graph import StateGraph
from langchain_core.memory import BaseMemory

from ai_core.langgraph.nodes.nodes import (
    load_memory_node,
    add_user_message_node,
    rephrase_input,
    detect_intent,
    safety_guard,
    retrieve_context,
    summarize_context,
    generate_response,
    generate_document,
    clarify_question,
    greet_user,
    deny_answer_confidently,
    log_query,
    add_ai_message_node,
    save_memory_node,
    simple_response,
    generate_summary
)
from ai_core.langgraph.nodes.related_free import RelatedFree
from ai_core.langgraph.nodes.cfg import inject_cfg

class GraphState(TypedDict, total=False):
    session_id: str
    question: str
    tier: Literal["free", "plus", "pro+"]   # injected at API layer
    niche: str                              # e.g. "immigration-usa"
    country: Optional[str] 
    clean_question: Optional[str]
    intent: Optional[str]
    is_safe: Optional[bool]
    docs: List[str]
    trimmed_docs: List[str]            # from summarization
    used_retrieval: bool
    answer: Optional[str]
    related_queries: List[str]
    # date‐filter fields
    recency_days: Optional[int]
    start_date: Optional[str]          # ISO date
    end_date: Optional[str]            # ISO date
    memory: Optional[BaseMemory]

def get_immigration_graph():
    g = StateGraph(GraphState)

    # ─── register nodes ────────────────────────────────────────────────────
    g.add_node("load_memory",       load_memory_node)
    g.add_node("inject_cfg",        inject_cfg)
    g.add_node("add_user_message",  add_user_message_node)
    g.add_node("rephrase_input",    rephrase_input)
    g.add_node("detect_intent",     detect_intent)
    g.add_node("safety_guard",      safety_guard)
    g.add_node("router",            lambda s: s)
    g.add_node("retrieve_context",   retrieve_context)
    g.add_node("summarize_context",  summarize_context)
    g.add_node("related_free",      RelatedFree())
    g.add_node("simple_response",    simple_response)     # new
    g.add_node("generate_summary",   generate_summary)    # new
    g.add_node("generate_response",  generate_response)
    g.add_node("generate_document", generate_document)
    g.add_node("clarify_question",  clarify_question)
    g.add_node("greet_user",        greet_user)
    g.add_node("deny_answer_confidently", deny_answer_confidently)
    g.add_node("log_query",         log_query)
    g.add_node("add_ai_message",    add_ai_message_node)
    g.add_node("save_memory",       save_memory_node)

    # ─── linear flow ───────────────────────────────────────────────────────
    g.set_entry_point("load_memory")
    g.add_edge("load_memory",      "inject_cfg")          # ③ first call cfg
    g.add_edge("inject_cfg",       "add_user_message")  
    g.add_edge("add_user_message", "rephrase_input")
    g.add_edge("rephrase_input",   "detect_intent")
    g.add_edge("detect_intent",    "safety_guard")

    # ─── safety branch ────────────────────────────────────────────────────
    g.add_conditional_edges(
        "safety_guard",
        lambda s: s["is_safe"],
        { True:  "router", False: "deny_answer_confidently" }
    )

    # ─── intent routing ───────────────────────────────────────────────────
    g.add_conditional_edges(
        "router",
        lambda s: s["intent"],
        {
            "greeting":       "greet_user",
            "generate_form":  "generate_document",
            "unclear":        "clarify_question",
            "simple_info":    "simple_response",   # new branch
            "summary":        "generate_summary",  # new branch
            # everything else → full RAG
            "ask_forecast":    "retrieve_context",
            "ask_form_info":   "retrieve_context",
            "state_law_query": "retrieve_context",
            "followup":        "retrieve_context",
            "not_in_docs":     "deny_answer_confidently",
        }
    )

    # ─── retrieval branch ─────────────────────────────────────────────────
    g.add_conditional_edges(
        "retrieve_context",
        lambda s: bool(s.get("docs")),
        { True:  "summarize_context", False: "deny_answer_confidently" }
    )

    # ─── summarization branch ─────────────────────────────────────────────
    g.add_edge("summarize_context", "related_free")
    g.add_edge("related_free", "generate_response")

    # ─── terminal nodes all flow into log_query ────────────────────────────
    for src in [
        "greet_user",
        "generate_response",
        "generate_document",
        "clarify_question",
        "deny_answer_confidently",
    ]:
        g.add_edge(src, "log_query")

    # ─── log and persist memory ────────────────────────────────────────────
    g.add_edge("log_query",      "add_ai_message")
    g.add_edge("add_ai_message", "save_memory")
    g.set_finish_point("save_memory")

    return g.compile()
