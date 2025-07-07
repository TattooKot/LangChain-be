import asyncio
import json
import uuid
import logging
from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI
from .config import settings
from .chime_repository import ChimeRepository
from .session_repository import SessionRepository

logger = logging.getLogger(__name__)
class ChatService:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.chime_repo = ChimeRepository()
        self.session_repo = SessionRepository()

    async def stream_chat_with_chime_updates(
        self,
        message: str,
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Implements the AWS Chime WebSocket flow:
        1. Send initial "Thinking..." message to Chime channel
        2. Stream OpenAI response and update the Chime message with each chunk
        3. Frontend receives WebSocket events from AWS Chime
        """

        # Step 1: Get or create session and channel
        if conversation_id:
            channel_arn = self.session_repo.get_channel_arn(conversation_id)
            if not channel_arn:
                raise ValueError(f"Session {conversation_id} not found")
        else:
            # Create new session
            conversation_id = str(uuid.uuid4())
            channel_name = f"chat-{conversation_id}"
            channel_arn = self.chime_repo.create_channel(channel_name)
            self.session_repo.create_session(conversation_id, channel_arn)

            # Yield the conversation ID to the client
            yield f"event: conversation_id\ndata: {conversation_id}\n\n"

        # Step 2: Add user message to channel
        self.chime_repo.append_message(channel_arn, message, "user")

        # Step 3: Send initial "Thinking..." message to Chime channel
        thinking_message_id = self.chime_repo.send_initial_message(
            channel_arn,
            "🤔 Thinking..."
        )

        # Step 4: Get conversation history for context
        history = self.chime_repo.get_history(channel_arn)

        # Prepare messages for OpenAI (exclude the "Thinking..." message)
        openai_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
            if msg["content"] != "🤔 Thinking..."
        ]

        # Step 5: Stream OpenAI response and update Chime message
        full_response = ""
        try:
            stream = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=openai_messages,
                stream=True,
                temperature=0.7,
                max_tokens=1000
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_response += token

                    # Step 6: Update the Chime message with accumulated response
                    self.chime_repo.update_channel_message(
                        channel_arn,
                        thinking_message_id,
                        full_response
                    )


        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.chime_repo.update_channel_message(
                channel_arn,
                thinking_message_id,
                error_msg
            )
            yield f"event: error\ndata: {error_msg}\n\n"

