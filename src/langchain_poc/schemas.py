from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = Field(
        default=None,
        description="UUID сесії. Якщо не заданий, сервер згенерує новий."
    )
