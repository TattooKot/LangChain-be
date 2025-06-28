from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from .config import settings
from .pipeline import pipeline
from .schemas import CapitalRequest, CapitalResponse
from openai import OpenAI
client = OpenAI(api_key=settings.OPENAI_API_KEY)

router = APIRouter()

@router.post(
    "/capital",
    response_model=CapitalResponse,
    summary="Отримати столицю країни",
    tags=["capital"]
)
async def get_capital(req: CapitalRequest):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")
    resp = pipeline.invoke({"country": req.country})
    return CapitalResponse(country=req.country, capital=resp.content)


@router.post(
    "/stream-capital",
    summary="Стрімінг відповіді: столиця країни токен за токеном",
    tags=["capital"],
)
async def stream_capital(req: CapitalRequest):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    def event_generator():
        # Пачка повідомлень для моделі
        messages = [{"role": "user", "content": f"What is the capital of {req.country}?"}]

        # Викликаємо новий метод chat.completions.create з stream=True
        for chunk in client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=messages,
                stream=True
        ):
            # У v1 API токени — в choices[0].delta.content
            delta = chunk.choices[0].delta.content
            if delta:
                yield f"data: {delta}\n\n"

        # Позначаємо кінець потоку
        yield "event: done\ndata: \n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )