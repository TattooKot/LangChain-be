from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse

from .schemas import ChatRequest
from .session_repository import SessionRepository
from .conversation_repository import ConversationRepository
from .chat_service import ChatService

router = APIRouter()
session_repo = SessionRepository()
convo_repo = ConversationRepository()
service = ChatService(session_repo, convo_repo)

@router.post("/stream-chat", summary="Streaming multi-turn chat")
async def stream_chat(req: ChatRequest, response: Response):
    # Залишаємо expose_headers для X-Conversation-ID
    response.headers["X-Conversation-ID"] = ""
    generator = service.stream_chat(req.message, req.conversation_id)
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Access-Control-Expose-Headers": "X-Conversation-ID",
        },
    )
