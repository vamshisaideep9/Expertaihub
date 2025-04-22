from langgraph.graph import StateGraph
from langchain_core.memory import BaseMemory
from ai_core.langgraph import nodes


#Langgraph state structure
from typing import TypedDict, Optional, List


class GraphState(TypedDict):
    question: str
    clean_question: Optional[str]
    intent: Optional[str]
    docs: Optional[List[str]]
    answer: Optional[str]
    niche: Optional[str]
    country: Optional[str]
    memory: Optional[BaseMemory]


def get_immigration_graph():
    workflow = StateGraph(GraphState)

    #Add all nodes
    workflow.add_node("rephrase_input", nodes.rephrase_input)
    workflow.add_node("detect_intent", nodes.detect_intent)
    workflow.add_node("retrieve_context", nodes.retrieve_context)
    workflow.add_node("generate_response", nodes.generate_response)
    workflow.add_node("generate_document", nodes.generate_document)
    workflow.add_node("clarify_question", nodes.clarify_question)
    workflow.add_node("log_query", nodes.log_query)


    #Define transitions
    workflow.set_entry_point("rephrase_input")
    workflow.add_edge("rephrase_input", "detect_intent")


    #Conditional branch on intent
    workflow.add_conditional_edges(
        "detect_intent",
        lambda state: state["intent"],

        {
            "ask_form_info": "retrieve_context",
            "state_law_query": "retrieve_context",
            "followup": "retrieve_context",
            "generate_form": "generate_document",
            "unclear": "clarify_question"
        }
    )


    # After retrieval → generate answer
    workflow.add_edge("retrieve_context", "generate_response")
    # Both generation paths → log and return
    workflow.add_edge("generate_response", "log_query")
    workflow.add_edge("generate_document", "log_query")


    # Done
    workflow.set_finish_point("log_query")

    return workflow.compile()

