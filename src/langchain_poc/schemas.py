from pydantic import BaseModel, Field
from typing import Optional, List

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Текст користувацького запиту")
    conversation_id: Optional[str] = Field(
        None, description="Наш internal session_id, якщо продовжуємо сесію"
    )

class SessionInfo(BaseModel):
    id: str = Field(..., description="Internal session_id")
    channel_arn: str = Field(..., description="ARN каналу у Chime SDK")

class SessionsResponse(BaseModel):
    sessions: List[SessionInfo] = Field(..., description="Список сесій із їх ARN")
