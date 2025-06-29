from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = Field(None, description="UUID session, generated if absent")
