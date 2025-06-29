from pydantic import BaseModel, Field
from typing import Optional, List

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = Field(
        None, description="UUID сесії. Якщо не заданий, сервер згенерує новий."
    )

class SessionsResponse(BaseModel):
    sessions: List[str] = Field(
        ..., description="Список всіх доступних conversation_id"
    )
