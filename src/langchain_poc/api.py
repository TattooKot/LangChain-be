from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from .routes import router

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
]

app = FastAPI(
    title="LangChain Stream Chat API",
    version="0.1.0",
    description="Streaming chat API with conversation memory",
    middleware=middleware,
)

app.include_router(router)
