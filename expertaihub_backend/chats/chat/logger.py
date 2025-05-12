from chats.models import ChatSession, ChatMessage


def log_chat(
    user,
    advisor=None,
    country=None,
    question: str = "",
    answer: str = "",
    session_id: str = None,
):
    """
    Logs one round of Q&A into ChatSession & ChatMessage.
    - On first call (no session_id): creates a new ChatSession
      (which will auto-generate its slug & session_id via model.save()).
    - On subsequent calls: looks up the existing session by session_id.
    Returns (slug, session_id)
    """

    # 1) Lookup or create the ChatSession
    if session_id:
        session = ChatSession.objects.filter(session_id=session_id, user=user).first()
    else:
        session = ChatSession.objects.create(
            user=user,
            advisor=advisor,
            country=country,
            title=question[:60],  # initial title from the first prompt
        )

    # 2) Persist the user’s question
    ChatMessage.objects.create(
        session=session,
        role="user",
        content=question,
    )
    # 3) Persist the AI’s answer
    ChatMessage.objects.create(
        session=session,
        role="ai",
        content=answer,
    )

    # 4) Return the identifiers for the frontend
    return session.slug, session.session_id
