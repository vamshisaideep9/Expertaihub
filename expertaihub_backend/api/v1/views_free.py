# views/immigration_free.py

import traceback
from datetime import date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import Throttled

from ai_core.langgraph.workflows.workflow_free import get_free_immigration_graph
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.memory import ConversationBufferMemory

from membership.models import MonthlyUsage
from ai_core.models import Advisor, Country

from chats.chat.logger import log_chat
from chats.models import ChatMessage

free_graph         = get_free_immigration_graph()
FREE_MONTHLY_LIMIT = 15

class FreeImmigrationAIView(APIView):
    def post(self, request):
        user = request.user
        today = date.today()
        period = today.replace(day=1)

        # 1) Quota check
        usage, _ = MonthlyUsage.objects.get_or_create(user=user, period=period)
        if usage.count >= FREE_MONTHLY_LIMIT:
            raise Throttled(detail="🚫 You’ve used all 15 free queries for this month.")

        # 2) Unpack inputs
        question     = request.data.get("question", "").strip()
        chat_history = request.data.get("chat_history", [])
        niche        = request.data.get("niche", "immigration")
        country_code = request.data.get("country", "usa")
        incoming_sid = request.data.get("session_id")

        if not question:
            return Response({"error": "Please provide a `question`."}, status=400)

        # 3) Build LangChain memory from supplied history
        buffer_memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            chat_memory=ChatMessageHistory(),
        )
        for msg in chat_history:
            if msg.get("role") == "user":
                buffer_memory.chat_memory.add_user_message(msg["content"])
            else:
                buffer_memory.chat_memory.add_ai_message(msg["content"])

        # 4) Wrap as follow-up if there's existing history
        if chat_history:
            follow_up = (
                "This is a follow-up question based on our previous conversation. "
                "Please answer only the new question without repeating the earlier explanation: "
                f"{question}"
            )
            buffer_memory.chat_memory.add_user_message(follow_up)
            prompt = follow_up
        else:
            buffer_memory.chat_memory.add_user_message(question)
            prompt = question

        # 5) Invoke the RAG graph
        state = {
            "question":       prompt,
            "niche":          niche,
            "country":        country_code,
            "memory":         buffer_memory,
            "used_retrieval": False,
        }
        try:
            state = free_graph.invoke(state)
        except Exception as e:
            traceback.print_exc()
            return Response({"error": f"Internal pipeline error: {e}"}, status=500)

        answer = state.get("answer", "").strip()

        # 6) Increment quota if retrieval happened
        if state.get("used_retrieval", False):
            usage.increment()

        # 7) Fetch advisor & country objects
        advisor = Advisor.objects.filter(slug=niche).first()
        country = Country.objects.filter(code=country_code).first()

        # 8) Log chat and get identifiers
        slug, session_id = log_chat(
            user=user,
            advisor=advisor,
            country=country,
            question=question,
            answer=answer,
            session_id=incoming_sid,
        )

        # 9) Rebuild canonical history from DB
        messages = ChatMessage.objects.filter(
            session__session_id=session_id
        ).order_by("created_at")
        canonical_history = [
            {"role": m.role, "content": m.content} for m in messages
        ]

        # 10) Build response
        first_time = incoming_sid is None
        response_data = {
            "answer":       answer,
            "chat_history": canonical_history,
            "quota": {
                "used":  usage.count,
                "limit": FREE_MONTHLY_LIMIT
            },
            "session_id": session_id,
        }
        if first_time:
            response_data["slug"] = slug

        return Response(response_data)
