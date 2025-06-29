from pydantic import BaseModel, Field
from typing import Optional, List

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Текст користувацького запиту")
    conversation_id: Optional[str] = Field(
        None, description="UUID сесії або ARN каналу Chime, якщо продовжуємо"
    )

class SessionsResponse(BaseModel):
    sessions: List[str] = Field(..., description="Список всіх ідентифікаторів сесій")
