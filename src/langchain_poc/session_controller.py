from fastapi import APIRouter
from .schemas import SessionsResponse
from .session_repository import SessionRepository

router = APIRouter(prefix="/sessions", tags=["sessions"])
repo = SessionRepository()

@router.get("", response_model=SessionsResponse, summary="Список усіх сесій")
async def list_sessions():
    return SessionsResponse(sessions=repo.list())

@router.delete("/{session_id}", response_model=SessionsResponse, summary="Видалити сесію")
async def delete_session(session_id: str):
    repo.delete(session_id)
    return SessionsResponse(sessions=repo.list())
