# ai_core/langgraph/workflow.py

from langgraph.graph import StateGraph
from langchain_core.memory import BaseMemory
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
    log_query
)
from typing import TypedDict, Optional, List

class GraphState(TypedDict):
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

    # 1) Add all nodes
    g.add_node("rephrase_input", rephrase_input)
    g.add_node("detect_intent", detect_intent)
    g.add_node("safety_guard", safety_guard)
    g.add_node("retrieve_context", retrieve_context)
    g.add_node("generate_response", generate_response)
    g.add_node("generate_document", generate_document)
    g.add_node("clarify_question", clarify_question)
    g.add_node("greet_user", greet_user)
    g.add_node("deny_answer_confidently", deny_answer_confidently)
    g.add_node("log_query", log_query)

    # 2) Entry point
    g.set_entry_point("rephrase_input")

    # 3) Straight‐line & conditional routing
    g.add_edge("rephrase_input", "detect_intent")

    # after intent, always do safety check
    g.add_edge("detect_intent", "safety_guard")

    # if unsafe → deny; if safe → intent router
    def router(state): return state
    g.add_node("router", router)
    g.add_conditional_edges(
        "safety_guard",
        lambda s: s["is_safe"],
        { True: "router", False: "deny_answer_confidently" }
    )

    # intent router
    g.add_conditional_edges(
        "router",
        lambda s: s["intent"],
        {
            "greeting":      "greet_user",
            "ask_form_info": "retrieve_context",
            "generate_form": "generate_document",
            "state_law_query":"retrieve_context",
            "followup":      "retrieve_context",
            "unclear":       "clarify_question",
            "not_in_docs":   "deny_answer_confidently"
        }
    )

    # finish chains
    g.add_edge("retrieve_context",      "generate_response")
    g.add_edge("generate_response",     "log_query")
    g.add_edge("generate_document",     "log_query")
    g.add_edge("clarify_question",      "log_query")
    g.add_edge("greet_user",            "log_query")
    g.add_edge("deny_answer_confidently","log_query")

    g.set_finish_point("log_query")
    return g.compile()
