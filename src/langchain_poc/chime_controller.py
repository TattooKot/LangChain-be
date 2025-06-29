from fastapi import APIRouter, Response, HTTPException
from fastapi.responses import StreamingResponse
from .schemas import ChatRequest
from .chat_service import ChatService

router = APIRouter(prefix="/chime", tags=["chime"])
service = ChatService()

@router.post(
    "/stream-chat",
    summary="Стрімінг чат через Chime SDK",
    response_class=StreamingResponse,
)
async def stream_chime_chat(req: ChatRequest, response: Response):
    # Додаємо заголовок із майбутнім ID (порожній перед стартом)
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
    except HTTPException as e:
        # Це спрацює, якщо, наприклад, OPENAI_API_KEY не заданий
        raise e
    except Exception as e:
        # Лог не падає у стрім — повернемо 500
        raise HTTPException(500, str(e))
