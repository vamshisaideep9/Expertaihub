import os
from langchain_openai import ChatOpenAI
from ai_core.rag.retriever import get_retriever
from langchain_core.messages import HumanMessage
from ai_core.prompts.prompts import rephrase_prompt, intent_prompt, generate_response_prompt


llm = ChatOpenAI(model="gpt-4o", temperature=0.3)




# 1. Rephrase (Optional Cleanup)

def rephrase_input(state):
    question = state["question"]
    chain = rephrase_prompt | llm | (lambda x: x.content.strip())
    clean_question = chain.invoke({"question": question})
    return {**state, "clean_question": clean_question}



def clarify_question(state):
    return {
        **state,
        "answer": "Could you please clarify what you're referring to?"
    }
   

def detect_intent(state):
    question = state["clean_question"]
    chain = intent_prompt | llm | (lambda x: x.content.strip())
    intent = chain.invoke({"question": question})
    return {**state, "intent": intent}





def retrieve_context(state):
    niche = state.get("niche", "immigration")
    country = state.get("country", "usa")
    question = state["clean_question"]
    retriever = get_retriever(niche, country)
    docs = retriever.invoke(question)
    return {"docs": [doc.page_content for doc in docs]}


def generate_response(state):
    question = state["clean_question"]
    context = "\n\n".join(state.get("docs", []))[:100000]
    memory = state.get("memory")

    history = ""
    if memory:
        for msg in memory.chat_memory.messages:
            role = "User" if isinstance(msg, HumanMessage) else "AI"
            history += f"{role}: {msg.content}"

    chain = generate_response_prompt | llm | (lambda x: x.content.strip())
    
    answer = chain.invoke({"question": question, "context": context})

    if memory:
        memory.chat_memory.add_user_message(question)
        memory.chat_memory.add_ai_message(answer)

    return {"answer": answer}







def generate_document(state):
    question = state["clean_question"]

    if "ar-11" in question.lower():
        return {"answer": "Here is your AR-11 form draft (to be implemented)."}
    
    return {"answer": "Document generation coming soon."}



def log_query(state):
    #print("🔎 Q:", state['clean_question'])
    #print("✅ A:", state['answer'])
    return state
    