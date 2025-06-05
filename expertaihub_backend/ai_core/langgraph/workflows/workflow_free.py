from typing import Optional, List, Dict, Any, TypedDict
from langgraph.graph import StateGraph
from langchain_core.memory import BaseMemory

from ai_core.langgraph.nodes.nodes import (
    load_memory_node, add_user_message_node,
    rephrase_input, detect_intent, safety_guard,
    retrieve_context, generate_response,
    generate_document, clarify_question,
    greet_user, deny_answer_confidently,
    log_query, add_ai_message_node,
    save_memory_node
)

class GraphState(TypedDict):
    session_id: str
    question: str
    clean_question: Optional[str]
    intent: Optional[str]
    is_safe: Optional[bool]
    docs: Optional[List[str]]
    used_retrieval: bool
    answer: Optional[str]
    niche: Optional[str]
    country: Optional[str]
    memory: Optional[BaseMemory]

def get_free_immigration_graph():
    g = StateGraph(GraphState)

    # 1) Register all nodes
    g.add_node("load_memory",       load_memory_node)
    g.add_node("add_user_message",  add_user_message_node)
    g.add_node("rephrase_input",    rephrase_input)
    g.add_node("detect_intent",     detect_intent)
    g.add_node("safety_guard",      safety_guard)
    g.add_node("router",            lambda s: s)
    g.add_node("retrieve_context",  retrieve_context)
    g.add_node("generate_response", generate_response)
    g.add_node("generate_document", generate_document)
    g.add_node("clarify_question",  clarify_question)
    g.add_node("greet_user",        greet_user)
    g.add_node("deny_answer_confidently", deny_answer_confidently)
    g.add_node("log_query",         log_query)
    g.add_node("add_ai_message",    add_ai_message_node)
    g.add_node("save_memory",       save_memory_node)

    # 2) Define entry & linear flow
    g.set_entry_point("load_memory")
    g.add_edge("load_memory",      "add_user_message")
    g.add_edge("add_user_message", "rephrase_input")
    g.add_edge("rephrase_input",   "detect_intent")
    g.add_edge("detect_intent",    "safety_guard")

    # 3) Safety branch
    g.add_conditional_edges(
        "safety_guard",
        lambda s: s["is_safe"],
        { True:  "router", False: "deny_answer_confidently" }
    )

    # 4) Intent routing
    g.add_conditional_edges(
        "router",
        lambda s: s["intent"],
        {
            # Purely static nodes:
            "greeting":      "greet_user",
            "generate_form": "generate_document",
            "unclear":       "clarify_question",
            # Everything else—even 'not_in_docs'—goes to RAG first:
            "ask_form_info":   "retrieve_context",
            "state_law_query": "retrieve_context",
            "followup":        "retrieve_context",
            "not_in_docs":     "deny_answer_confidently",  
        }
    )

    # 5) RAG branch: only if docs found → generate_response; else deny
    g.add_conditional_edges(
        "retrieve_context",
        lambda s: bool(s.get("docs")),
        { True:  "generate_response", False: "deny_answer_confidently" }
    )

    # 6) All terminal nodes → log_query
    for src in ["greet_user","generate_response","generate_document","clarify_question","deny_answer_confidently"]:
        g.add_edge(src, "log_query")

    # 7) Log → memory write → finish
    g.add_edge("log_query",      "add_ai_message")
    g.add_edge("add_ai_message", "save_memory")
    g.set_finish_point("save_memory")

    return g.compile()
