import uuid
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse

from .config import settings
from .schemas import CapitalRequest, CapitalResponse
from .pipeline import pipeline  # ваш LangChain-пайплайн

router = APIRouter()

@router.post(
    "/capital",
    response_model=CapitalResponse,
    summary="Синхронне повернення столиці з conversation_id",
    tags=["capital"],
)
async def get_capital(req: CapitalRequest):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    # згенеруємо або підхопимо існуючий ID
    conv_id = req.conversation_id or str(uuid.uuid4())

    # отримуємо столицю
    resp = pipeline.invoke({"country": req.country})

    # повертаємо разом із ID
    return CapitalResponse(
        country=req.country,
        capital=resp.content,
        conversation_id=conv_id,
    )


@router.post(
    "/stream-capital",
    summary="Стрімінг відповіді з conversation_id",
    tags=["capital"],
)
async def stream_capital(req: CapitalRequest, response: Response):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    # згенеруємо або підхопимо існуючий ID
    conv_id = req.conversation_id or str(uuid.uuid4())

    # додаємо його в заголовки відповіді — клієнт може зчитати X-Conversation-ID
    response.headers["X-Conversation-ID"] = conv_id

    def event_generator():
        # спочатку відправимо окрему подію з ID (як custom SSE event)
        yield f"event: conversation_id\ndata: {conv_id}\n\n"

        # тепер сам стрім токенів
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        messages = [{"role": "user", "content": f"What is the capital of {req.country}?"}]

        for chunk in client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=messages,
                stream=True
        ):
            delta = chunk.choices[0].delta.content
            if delta:
                yield f"event: token\ndata: {delta}\n\n"

        # сигналізуємо кінець потоку
        yield "event: done\ndata: \n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
