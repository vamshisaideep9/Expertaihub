# views/immigration_free.py

from datetime import date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import Throttled
from ai_core.langgraph.workflows.workflow_free import get_free_immigration_graph
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.memory import ConversationBufferMemory
from membership.models import MonthlyUsage
from chats.models import ChatLibrary
from ai_core.models import Advisor, Country
from chats.chat.logger import log_chat

free_graph         = get_free_immigration_graph()
FREE_MONTHLY_LIMIT = 15

class FreeImmigrationAIView(APIView):
    def post(self, request):
        user = request.user
        today = date.today()
        period = today.replace(day=1)

        # 1) Get or create this month's usage bucket
        usage, _ = MonthlyUsage.objects.get_or_create(user=user, period=period)
        if usage.count >= FREE_MONTHLY_LIMIT:
            raise Throttled(detail="🚫 You’ve used all 15 free queries for this month.")

        # 2) Unpack inputs
        question     = request.data.get("question", "").strip()
        chat_history = request.data.get("chat_history", [])
        niche        = request.data.get("niche", "immigration")
        country_code = request.data.get("country", "usa")
        session_id   = request.data.get("session_id") 

        if not question:
            return Response({"error": "Please provide a `question`."}, status=400)
        buffer_memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            chat_memory=ChatMessageHistory()
        )
        for msg in chat_history:
            role, content = msg.get("role"), msg.get("content")
            if role == "user":
                buffer_memory.chat_memory.add_user_message(content)
            elif role == "ai":
                buffer_memory.chat_memory.add_ai_message(content)
        buffer_memory.chat_memory.add_user_message(question)

    
        state = {
            "question":       question,
            "niche":          niche,
            "country":        country_code,
            "memory":         buffer_memory,
            "used_retrieval": False,   
        }
        try:
            state = free_graph.invoke(state)
        except Exception as e:
            return Response({"error": f"Internal pipeline error: {e}"}, status=500)

        answer = state.get("answer", "").strip()
        updated_history = chat_history + [
            {"role": "user", "content": question},
            {"role": "ai",   "content": answer},
        ]


        if state.get("used_retrieval", False):
            usage.increment()
        advisor = Advisor.objects.filter(slug=niche).first()
        country = Country.objects.filter(code=country_code).first()
        slug = log_chat(user, advisor, country, question, answer, session_id=session_id)

        entry = ChatLibrary.objects.get(user=user, slug=slug)
        session_obj = entry.session


        first_time = session_id is None
        response_data = {
            "answer":       answer,
            "chat_history": updated_history,
            "quota": {
                "used":  usage.count,
                "limit": FREE_MONTHLY_LIMIT
            },
            "session_id": session_obj.session_id,
        }
        if first_time:
            response_data["slug"] = session_obj.slug

        return Response(response_data)
