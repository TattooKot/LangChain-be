from typing import Generator
from openai import OpenAI
from fastapi import HTTPException

from .config import settings
from .session_repository import SessionRepository
from .conversation_repository import ConversationRepository  # ваш існ. in-memory

class ChatService:
    def __init__(self,
                 session_repo: SessionRepository,
                 convo_repo: ConversationRepository
                 ):
        if not settings.OPENAI_API_KEY:
            raise HTTPException(500, "OPENAI_API_KEY not set")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.session_repo = session_repo
        self.convo_repo = convo_repo

    def stream_chat(self, message: str, conv_id: str | None) -> Generator[str, None, None]:
        # Якщо немає conv_id — створюємо нову сесію в БД
        if not conv_id:
            conv_id = self.session_repo.create_session()
        # Мати паралельно й in-memory історію
        history = self.convo_repo.get_history(conv_id)
        self.convo_repo.append_user(conv_id, message)

        # 1) event: conversation_id
        yield f"event: conversation_id\ndata: {conv_id}\n\n"

        # 2) stream token-ами
        tokens = []
        for chunk in self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=history,
                stream=True
        ):
            delta = chunk.choices[0].delta.content
            if delta:
                tokens.append(delta)
                yield f"event: token\ndata: {delta}\n\n"

        # 3) завершуємо історію
        full = "".join(tokens)
        self.convo_repo.append_assistant(conv_id, full)

        # 4) done
        yield "event: done\ndata: \n\n"
