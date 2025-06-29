import uuid
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse

from .config import settings
from .schemas import ChatRequest
from openai import OpenAI  # v1 API

router = APIRouter()

# In-memory сховище історії
conversations: dict[str, list[dict]] = {}

client = OpenAI(api_key=settings.OPENAI_API_KEY)

@router.post(
    "/stream-chat",
    summary="Стрімінг багатокрокової розмови з conversation_id",
    tags=["chat"],
)
async def stream_chat(req: ChatRequest, response: Response):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(500, "OPENAI_API_KEY not set")

    conv_id = req.conversation_id or str(uuid.uuid4())
    history = conversations.setdefault(conv_id, [])
    history.append({"role": "user", "content": req.message})

    # Додаємо ID у заголовок
    response.headers["X-Conversation-ID"] = conv_id

    def event_generator():
        # 1) Шлемо conversation_id
        yield f"event: conversation_id\ndata: {conv_id}\n\n"

        # 2) Стрімимо токени та накопичуємо їх
        full_reply_tokens: list[str] = []
        for chunk in client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=history,
                stream=True,
        ):
            token = chunk.choices[0].delta.content
            if token:
                full_reply_tokens.append(token)
                yield f"event: token\ndata: {token}\n\n"

        # 3) Після стріму — збираємо повну відповідь
        full_reply = "".join(full_reply_tokens)
        history.append({"role": "assistant", "content": full_reply})

        # 4) Сигнал закінчення
        yield "event: done\ndata: \n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
