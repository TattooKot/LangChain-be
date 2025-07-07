from fastapi import APIRouter, Response, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
import logging

from .schemas import ChatRequest
from .chat_service import ChatService
from .chime_repository import ChimeRepository
from .session_repository import SessionRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chime", tags=["chime"])
service = ChatService()
chime_repo = ChimeRepository()
session_repo = SessionRepository()

@router.post(
    "/stream-chat",
    summary="Стрімінг чат через Chime SDK",
    response_class=StreamingResponse,
)
async def stream_chime_chat(req: ChatRequest, response: Response):
    # у ChatService тепер приймаємо internal session_id і автоматично створюємо
    # новий канал + запис у Postgres, якщо req.conversation_id==None
    response.headers["X-Conversation-ID"] = ""
    try:
        gen = service.stream_chat(req.message, req.conversation_id)
        return StreamingResponse(
            gen,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Expose-Headers": "X-Conversation-ID",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get(
    "/history/{session_id}",
    summary="Отримати всю історію повідомлень для internal session_id",
    response_model=List[dict],
)
async def get_chime_history(session_id: str):
    # витягаємо ARN з Postgres
    arn = session_repo.get_channel_arn(session_id)
    if not arn:
        raise HTTPException(404, "Session not found")
    try:
        history = chime_repo.get_history(arn)
        return history
    except Exception as e:
        raise HTTPException(500, f"Cannot fetch history: {e}")


@router.get(
    "/websocket-url/{session_id}",
    summary="Get AWS Chime WebSocket URL for a session",
)
async def get_chime_websocket_url(session_id: str):
    """
    Get the AWS Chime WebSocket URL for direct connection from frontend.
    This eliminates the need for a backend WebSocket proxy.
    """
    try:
        # Get the channel ARN for this session
        channel_arn = session_repo.get_channel_arn(session_id)
        if not channel_arn:
            raise HTTPException(404, "Session not found")
        
        # Get the WebSocket URL from Chime
        websocket_url = chime_repo.get_websocket_url()
        
        return {
            "websocket_url": websocket_url,
            "session_id": session_id,
            "channel_arn": channel_arn
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting WebSocket URL: {e}")
        raise HTTPException(500, f"Cannot get WebSocket URL: {e}")
