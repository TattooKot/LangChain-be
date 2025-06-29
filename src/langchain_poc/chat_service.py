from typing import Generator, Optional
from openai import OpenAI
from fastapi import HTTPException

from .config import settings
from .session_repository import SessionRepository
from .chime_repository import ChimeRepository

class ChatService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise HTTPException(500, "OPENAI_API_KEY not set")
        self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.sessions = SessionRepository()
        self.chime    = ChimeRepository()

    def stream_chat(
            self, message: str, session_id: Optional[str]
    ) -> Generator[str, None, None]:
        # 1) Якщо session_id заданий і є в БД — витягаємо його ARN, інакше створюємо новий канал + запис
        if session_id:
            arn = self.sessions.get_channel_arn(session_id)
            if not arn:
                raise HTTPException(404, "Session not found")
        else:
            arn = self.chime.create_channel()
            session_id = self.sessions.create(arn)

        # 2) Додаємо user-повідомлення до Chime
        self.chime.append_message(arn, message, sender_role="user")

        # 3) SSE: спочатку віддаємо internal session_id
        yield f"event: conversation_id\ndata: {session_id}\n\n"

        # 4) Підтягуємо історію
        history = self.chime.get_history(arn)

        # 5) Стрімимо токени з LLM
        tokens: list[str] = []
        for chunk in self.llm.chat.completions.create(
                model="gpt-4.1-nano", messages=history, stream=True
        ):
            delta = chunk.choices[0].delta.content
            if delta:
                tokens.append(delta)
                yield f"event: token\ndata: {delta}\n\n"

        full = "".join(tokens)
        # 6) Додаємо відповідь асистента в Chime
        self.chime.append_message(arn, full, sender_role="assistant")
        # 7) Сигнал завершення
        yield "event: done\ndata: \n\n"
