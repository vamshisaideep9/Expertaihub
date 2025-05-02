# chats/chat/logger.py

import secrets
from django.utils.text import slugify
from chats.models import ChatSession, ChatMessage, ChatLibrary

def log_chat(user, advisor, country, question, answer, session_id=None):
    """
    Create or update a chat session and log both user and AI messages.
    Also save a summarized version in ChatLibrary and return the slug.
    """
    session = None

    if session_id:
        session = ChatSession.objects.filter(session_id=session_id, user=user).first()

    if not session:
        session = ChatSession.objects.create(
            user=user,
            advisor=advisor,
            country=country,
            title=question[:60],
        )

    # Save user & AI messages
    ChatMessage.objects.create(session=session, sender="user", content=question)
    ChatMessage.objects.create(session=session, sender="ai", content=answer)

    # Build unique slug
    base_slug = slugify(question)[:60]
    unique_slug = f"{base_slug}-{secrets.token_hex(4)}"

    # Save to ChatLibrary (or update)
    entry, _ = ChatLibrary.objects.get_or_create(
        user=user,
        session=session,
        defaults={
            "prompt": question,
            "answer": answer,
            "advisor": advisor,
            "country": country,
            "slug": unique_slug,
        }
    )

    return entry.slug


