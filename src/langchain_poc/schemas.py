# schemas.py
from pydantic import BaseModel, Field
from typing import Optional

class CapitalRequest(BaseModel):
    country: str
    conversation_id: Optional[str] = Field(
        default=None,
        description="UUID діалогу. Якщо не заданий — буде згенерований новий."
    )

class CapitalResponse(BaseModel):
    country: str
    capital: str
    conversation_id: str  # обов’язково повертаємо в відповіді
