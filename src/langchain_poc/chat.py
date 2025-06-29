from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
from .schemas import ChatRequest
from .conversation_repository import ConversationRepository
from .chat_service import ChatService

router = APIRouter()
_repo = ConversationRepository()
_service = ChatService(_repo)

@router.post("/stream-chat", summary="Streaming multi-turn chat")
async def stream_chat(req: ChatRequest, response: Response):
    response.headers["X-Conversation-ID"] = ""  # FastAPI автоматично збере після першого yield
    generator = _service.stream_chat(req.message, req.conversation_id)
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Access-Control-Expose-Headers": "X-Conversation-ID"},
    )
