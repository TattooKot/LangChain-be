from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from .session_controller import router as sessions_router
from .chime_controller    import router as chime_router

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Conversation-ID"],
    )
]

app = FastAPI(
    title="LangChain + Chime Hybrid Chat API",
    version="0.1.0",
    middleware=middleware
)

app.include_router(sessions_router)   # /sessions
app.include_router(chime_router)      # /chime/stream-chat
