# chats/views.py

from datetime import date
import traceback

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_core.langgraph.workflows.workflow_free import get_free_immigration_graph
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.memory import ConversationBufferMemory

from membership.models import MonthlyUsage
from ai_core.models import Advisor, Country

from .models import ChatSession, ChatMessage
from .serializers import (
    ChatSessionSerializer,
    ChatSessionDetailSerializer,
    ChatMessageSerializer,
)
from chats.chat.logger import log_chat

free_graph = get_free_immigration_graph()
FREE_MONTHLY_LIMIT = 15


class ChatSessionViewSet(viewsets.ModelViewSet):
    permission_classes  = [IsAuthenticated]
    lookup_field        = "slug"
    filterset_fields    = ["archived", "created_at", "title", "pinned"]
    ordering_fields     = ["created_at", "updated_at", "title"]
    http_method_names   = ["get", "post", "patch", "delete"]  # allow PATCH

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ChatSessionDetailSerializer
        return ChatSessionSerializer

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, slug=None):
        session = self.get_object()
        session.archived = True
        session.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="chat")
    def chat(self, request, slug=None):
        """
        Continue a chat in this session.
        POST /api/library/{slug}/chat/
        Body: { question, niche?, country? }
        """
        user    = request.user
        session = get_object_or_404(ChatSession, slug=slug, user=user)

        # 1) Quota check
        today   = date.today()
        period  = today.replace(day=1)
        usage, _ = MonthlyUsage.objects.get_or_create(user=user, period=period)
        if usage.count >= FREE_MONTHLY_LIMIT:
            return Response({"detail": "🚫 Out of free queries"}, status=429)

        # 2) Unpack
        question     = request.data.get("question", "").strip()
        niche        = request.data.get("niche", "immigration")
        country_code = request.data.get("country", "usa")

        if not question:
            return Response({"error": "Please provide a `question`."}, status=400)

        # 3) Build memory from DB
        buffer_memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            chat_memory=ChatMessageHistory(),
        )
        for m in session.messages.order_by("created_at"):
            if m.role == "user":
                buffer_memory.chat_memory.add_user_message(m.content)
            else:
                buffer_memory.chat_memory.add_ai_message(m.content)
        buffer_memory.chat_memory.add_user_message(question)

        # 4) Invoke RAG
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
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)

        answer = state.get("answer", "").strip()

        # 5) Record messages
        ChatMessage.objects.create(session=session, role="user", content=question)
        ChatMessage.objects.create(session=session, role="ai",   content=answer)

        # 6) Increment quota if used retrieval
        if state.get("used_retrieval", False):
            usage.increment()

        # 7) Return full history
        history = [
            {"role": m.role, "content": m.content}
            for m in session.messages.order_by("created_at")
        ]

        return Response({
            "answer":       answer,
            "chat_history": history,
            "quota":        {"used": usage.count, "limit": FREE_MONTHLY_LIMIT},
            "session_id":   session.session_id,
        })


class ChatMessageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = get_object_or_404(ChatSession, session_id=session_id, user=request.user)
        msgs    = session.messages.order_by("created_at")
        return Response(ChatMessageSerializer(msgs, many=True).data)
