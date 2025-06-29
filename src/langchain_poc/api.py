from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from .routes import router

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],      # у продакшні краще конкретний домен
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
]
app = FastAPI(
    title="LangChain Capital API",
    version="0.1.0",
    description="Returns the capital of a given country using GPT-4.1-nano via LangChain pipeline",
    middleware=middleware
)

# Підключаємо наш router
app.include_router(router, prefix="", tags=["capital"])
