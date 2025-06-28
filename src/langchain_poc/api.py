from fastapi import FastAPI
from .routes import router

app = FastAPI(
    title="LangChain Capital API",
    version="0.1.0",
    description="Returns the capital of a given country using GPT-4.1-nano via LangChain pipeline"
)

# Підключаємо наш router
app.include_router(router, prefix="", tags=["capital"])
