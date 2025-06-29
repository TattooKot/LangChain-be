from typing import Generator, Optional
from fastapi import HTTPException
import uuid

from .config import settings
from .session_repository import SessionRepository
from .chime_repository import ChimeRepository

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

class ChatService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise HTTPException(500, "OPENAI_API_KEY not set")
        if not settings.CHIME_APP_INSTANCE_ARN or not settings.CHIME_APP_INSTANCE_USER_ARN:
            raise HTTPException(500, "Chime settings not set")

        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-4.1-nano",
            streaming=True,
        )
        self.sessions = SessionRepository()
        self.chime = ChimeRepository()

    def stream_chat(
            self, message: str, session_id: Optional[str]
    ) -> Generator[str, None, None]:
        # 1) Якщо internal session_id є — отримуємо ARN, інакше створюємо нову сесію + канал
        if session_id:
            arn = self.sessions.get_channel_arn(session_id)
            if not arn:
                raise HTTPException(404, "Session not found")
        else:
            session_id = str(uuid.uuid4())
            arn = self.chime.create_channel(name=f"chat-{session_id}")
            self.sessions.create(session_id, arn)

        # 2) Додаємо user-повідомлення до Chime
        self.chime.append_message(arn, message, sender_role="user")

        # 3) SSE: спочатку віддаємо internal session_id
        yield f"event: conversation_id\ndata: {session_id}\n\n"

        # 4) Підтягуємо історію з Chime
        history = self.chime.get_history(arn)

        # 5) Формуємо LangChain messages
        lc_messages = []
        for m in history:
            if m["role"] == "user":
                lc_messages.append(HumanMessage(content=m["content"]))
            else:
                lc_messages.append(AIMessage(content=m["content"]))

        lc_messages.append(HumanMessage(content=message))

        # 5) Стрімимо токени з LLM через LangChain
        tokens: list[str] = []
        def on_token(token):
            tokens.append(token)
            yield f"event: token\ndata: {token}\n\n"

        # LangChain streaming: use the .stream method
        yield from self._stream_langchain(lc_messages, tokens)

        full_response = "".join(tokens)

        # 6) Додаємо відповідь асистента в Chime
        self.chime.append_message(arn, full_response, sender_role="assistant")

        # 7) Сигнал завершення
        yield "event: done\ndata: \n\n"

    def _stream_langchain(self, lc_messages, tokens):
        # LangChain's .stream yields tokens
        for chunk in self.llm.stream(lc_messages):
            if hasattr(chunk, "content") and chunk.content:
                tokens.append(chunk.content)
                yield f"event: token\ndata: {chunk.content}\n\n"
