import uuid
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse

from .config import settings
from .schemas import ChatRequest
from openai import OpenAI

router = APIRouter()

# In-memory сховище історій: {conversation_id: [{"role":..., "content":...}, ...]}
conversations: dict[str, list[dict]] = {}

# Ініціалізуємо клієнт once
client = OpenAI(api_key=settings.OPENAI_API_KEY)

@router.post(
    "/stream-chat",
    summary="Стрімінг багатокрокової розмови з conversation_id",
    tags=["chat"],
)
async def stream_chat(req: ChatRequest, response: Response):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    # Генеруємо або підхоплюємо UUID
    conv_id = req.conversation_id or str(uuid.uuid4())
    # Підхоплюємо історію або ініціалізуємо нову
    history = conversations.setdefault(conv_id, [])
    # Додаємо нове user-повідомлення
    history.append({"role": "user", "content": req.message})

    # Віддаємо ID в заголовку
    response.headers["X-Conversation-ID"] = conv_id

    def event_generator():
        # Спочатку сповіщаємо про conversation_id
        yield f"event: conversation_id\ndata: {conv_id}\n\n"

        # Стрімимо відповідь токен за токеном
        for chunk in client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=history,
                stream=True
        ):
            token = chunk.choices[0].delta.content
            if token:
                yield f"event: token\ndata: {token}\n\n"

        # Після завершення збираємо повну відповідь
        # і зберігаємо її в історії
        full_reply = "".join(
            c.choices[0].delta.content
            for c in client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=history,
                stream=True
            )
        )
        history.append({"role": "assistant", "content": full_reply})

        # Сигналізуємо кінець
        yield "event: done\ndata: \n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
