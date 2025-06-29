from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from .chat import router as chat_router

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Conversation-ID"],
    )
]

app = FastAPI(middleware=middleware)
app.include_router(chat_router)
