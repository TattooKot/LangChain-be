from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
from .schemas import ChatRequest, SessionsResponse
from .session_repository import SessionRepository
from .conversation_repository import ConversationRepository
from .chat_service import ChatService

router = APIRouter()
session_repo = SessionRepository()
convo_repo   = ConversationRepository()
service      = ChatService(session_repo, convo_repo)

@router.post(
    "/stream-chat",
    summary="Стрімінг багатокрокової розмови з conversation_id",
    tags=["chat"],
)
async def stream_chat(req: ChatRequest, response: Response):
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

@router.get(
    "/sessions",
    response_model=SessionsResponse,
    summary="Повернути список всіх conversation_id",
    tags=["chat"],
)
async def list_sessions():
    ids = session_repo.list_sessions()
    return SessionsResponse(sessions=ids)

@router.delete(
    "/sessions/{conversation_id}",
    response_model=SessionsResponse,
    summary="Видалити одну сесію за conversation_id",
    tags=["chat"],
)
async def delete_session(conversation_id: str):
    # видаляємо із БД
    session_repo.delete_session(conversation_id)
    # також можна очистити in-memory історію, якщо потрібно
    # from .conversation_repository import conversations
    # conversations.pop(conversation_id, None)
    # повертаємо оновлений список
    ids = session_repo.list_sessions()
    return SessionsResponse(sessions=ids)
