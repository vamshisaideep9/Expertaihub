import logging
from langchain.memory.buffer import ConversationBufferMemory
from chats.models import ChatMessage

logger = logging.getLogger(__name__)

class MemoryStore:
    @staticmethod
    def load_for(session_id: str) -> ConversationBufferMemory:
        logger.info(f"[MemoryStore] Loading memory for session_id={session_id}")
        mem = ConversationBufferMemory(return_messages=True)
        qs = ChatMessage.objects.filter(
            session__session_id=session_id
        ).order_by("timestamp")  # use your actual timestamp field
        count = qs.count()
        for m in qs:
            if m.role == "user":
                mem.chat_memory.add_user_message(m.content)
            else:
                mem.chat_memory.add_ai_message(m.content)
        logger.info(f"[MemoryStore] Loaded {count} messages into memory")
        return mem

    @staticmethod
    def save_for(session_id: str, mem: ConversationBufferMemory):
        total = len(mem.chat_memory.messages)
        logger.info(f"[MemoryStore] Memory for session_id={session_id} now holds {total} turns")
