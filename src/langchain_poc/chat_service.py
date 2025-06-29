from typing import Generator
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

    def stream_chat(self, message: str, conv_id: str | None) -> Generator[str, None, None]:
        # 1. Забезпечити існування сесії в Postgres
        if conv_id:
            session_id = conv_id
        else:
            session_id = self.sessions.create()
        # 2. Забезпечити існування каналу в Chime
        #    (ми просто використовуємо session_id як ARN, тому якщо це не ARN, створимо новий канал)
        if session_id.startswith("arn:"):
            channel_arn = session_id
        else:
            channel_arn = self.chime.create_channel()
        # 3. Додаємо user-повідомлення в Chime
        self.chime.append_message(channel_arn, message, sender_role="user")
        # 4. SSE: спочатку повертаємо ідентифікатор сесії
        yield f"event: conversation_id\ndata: {session_id}\n\n"
        # 5. Підтягуємо всю історію з Chime
        history = self.chime.get_history(channel_arn)
        # 6. Стрімимо від LLM
        tokens: list[str] = []
        for chunk in self.llm.chat.completions.create(
                model="gpt-4.1-nano", messages=history, stream=True
        ):
            delta = chunk.choices[0].delta.content
            if delta:
                tokens.append(delta)
                yield f"event: token\ndata: {delta}\n\n"
        full = "".join(tokens)
        # 7. Зберігаємо відповідь асистента в Chime
        self.chime.append_message(channel_arn, full, sender_role="assistant")
        # 8. Сигнал готовності
        yield "event: done\ndata: \n\n"
