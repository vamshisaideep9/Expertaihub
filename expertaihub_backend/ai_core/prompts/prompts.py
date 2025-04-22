from langchain_core.prompts import ChatPromptTemplate


rephrase_prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant that clarifies vague user questions for better understanding.
If the question includes pronouns like "it", "this", or "that" without clear reference, keep them as-is or flag the question as ambiguous.

Input: "{question}"
Output (rephrased or flagged):""")


intent_prompt = ChatPromptTemplate.from_template("""
Classify the user's question into one of the following intents:

- ask_form_info
- generate_form
- state_law_query
- followup
- unclear

Question: "{question}"

Intent:
""")



generate_response_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert immigration advisor. Only answer based on the context provided. Do not assume anything not mentioned in the question."),
    ("human", """
Context:
{context}

User Question:
{question}

Answer (be concise, professional, and clarify if necessary):
""")
])
