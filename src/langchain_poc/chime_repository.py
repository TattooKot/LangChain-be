# src/langchain_poc/chime_repository.py

import uuid
import boto3
from typing import List
from .config import settings

class ChimeRepository:
    def __init__(self):
        self.client = boto3.client(
            "chime-sdk-messaging",
            region_name=settings.AWS_REGION,
        )
        self.app_inst_arn = settings.CHIME_APP_INSTANCE_ARN
        self.user_arn     = settings.CHIME_APP_INSTANCE_USER_ARN

    def create_channel(self) -> str:
        resp = self.client.create_channel(
            AppInstanceArn=self.app_inst_arn,
            Name=str(uuid.uuid4()),
            Mode="RESTRICTED",
            Privacy="PRIVATE",
            ChimeBearer=self.user_arn,
        )
        arn = resp["ChannelArn"]
        # Додаємо користувача в канал
        self.client.create_channel_membership(
            ChannelArn=arn,
            MemberArn=self.user_arn,
            Type="DEFAULT",
            ChimeBearer=self.user_arn,
        )
        return arn

    def delete_channel(self, channel_arn: str) -> None:
        self.client.delete_channel(
            ChannelArn=channel_arn,
            ChimeBearer=self.user_arn,
        )

    def append_message(self, channel_arn: str, content: str, sender_role: str) -> None:
        self.client.send_channel_message(
            ChannelArn=channel_arn,
            Content=content,
            Persistence="PERSISTENT",
            Type="STANDARD",
            ChimeBearer=self.user_arn,
        )

    def get_history(self, channel_arn: str) -> List[dict]:
        """
        Завантажує всю історію повідомлень із вказаного каналу,
        обробляючи NextToken, бо list_channel_messages не підтримує пагінатор.
        """
        messages = []
        next_token = None

        while True:
            params = {
                "ChannelArn": channel_arn,
                "ChimeBearer": self.user_arn,
                "SortOrder": "ASCENDING",
                "MaxResults": 50,  # макс. 50 на виклик
            }
            if next_token:
                params["NextToken"] = next_token

            resp = self.client.list_channel_messages(**params)
            for m in resp.get("ChannelMessages", []):
                role = "user" if m["Sender"] == self.user_arn else "assistant"
                messages.append({"role": role, "content": m["Content"]})

            next_token = resp.get("NextToken")
            if not next_token:
                break

        return messages
