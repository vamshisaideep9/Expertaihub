from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ai_core.langgraph.workflow import get_immigration_graph
from langchain.memory import ChatMessageHistory
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain_openai import ChatOpenAI

llm_for_summary = ChatOpenAI(model="gpt-4o", temperature=0)
graph_executor = get_immigration_graph()

class ImmigrationAIView(APIView):
    def post(self, request):
        try:
            question = request.data.get("question")
            niche = request.data.get("niche", "immigration")
            country = request.data.get("country", "usa")

            if not question:
                return Response({"error": "Question is required."}, status=status.HTTP_400_BAD_REQUEST)

            buffer_memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                chat_memory=ChatMessageHistory()
            )

            summary_memory = ConversationSummaryMemory(
                llm=llm_for_summary,
                memory_key="history",
                return_messages=True
            )

            past = request.session.get("chat_history", [])
            past_summary = request.session.get("chat_summary", "")

            for turn in past:
                buffer_memory.chat_memory.add_user_message(turn["user"])
                buffer_memory.chat_memory.add_ai_message(turn["ai"])

            if past_summary:
                summary_memory.buffer = past_summary

    
            state = {
                "question": question,
                "niche": niche,
                "country": country,
                "memory": summary_memory
            }

            result = graph_executor.invoke(state)
            answer = result.get("answer")

            buffer_memory.chat_memory.add_user_message(question)
            buffer_memory.chat_memory.add_ai_message(answer)

            past.append({"user": question, "ai": answer})
            request.session['chat_history'] = past
            request.session['chat_summary'] = summary_memory.buffer

            return Response({
                "answer": answer,
                "chat_history": past  
            })

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
