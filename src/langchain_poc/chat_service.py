import uuid
from typing import Generator
from openai import OpenAI
from fastapi import HTTPException
from .config import settings
from .conversation_repository import ConversationRepository

class ChatService:
    def __init__(self, repo: ConversationRepository):
        if not settings.OPENAI_API_KEY:
            raise HTTPException(500, "OPENAI_API_KEY not set")
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self._repo = repo

    def _ensure_conversation(self, conv_id: str | None) -> str:
        return conv_id or str(uuid.uuid4())

    def stream_chat(self, message: str, conv_id: str | None) -> Generator[str, None, None]:
        conv_id = self._ensure_conversation(conv_id)
        history = self._repo.get_history(conv_id)
        # append user
        self._repo.append_user(conv_id, message)

        # 1) conversation_id event
        yield f"event: conversation_id\ndata: {conv_id}\n\n"

        # 2) stream tokens
        tokens: list[str] = []
        for chunk in self._client.chat.completions.create(
                model="gpt-4.1-nano", messages=history, stream=True
        ):
            delta = chunk.choices[0].delta.content
            if delta:
                tokens.append(delta)
                yield f"event: token\ndata: {delta}\n\n"

        full = "".join(tokens)
        # 3) append assistant
        self._repo.append_assistant(conv_id, full)

        # 4) done event
        yield "event: done\ndata: \n\n"
