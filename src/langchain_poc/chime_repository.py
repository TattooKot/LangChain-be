# src/langchain_poc/chime_repository.py

import json
import boto3
from typing import List, Dict, Any
from .config import settings

class ChimeRepository:
    def __init__(self):
        self.client = boto3.client(
            "chime-sdk-messaging",
            region_name=settings.AWS_REGION,
        )
        self.app_inst_arn = settings.CHIME_APP_INSTANCE_ARN
        self.user_arn     = settings.CHIME_APP_INSTANCE_USER_ARN

    def create_channel(self, name: str) -> str:
        """
        Створює новий канал із заданим ім'ям і повертає його ARN.
        """
        resp = self.client.create_channel(
            AppInstanceArn=self.app_inst_arn,
            Name=name,
            Mode="RESTRICTED",
            Privacy="PRIVATE",
            ChimeBearer=self.user_arn,
        )
        arn = resp["ChannelArn"]
        # Додаємо нашого користувача до новоствореного каналу
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
        """
        Надсилає повідомлення до каналу з metadata, де зберігаємо роль відправника.
        """
        metadata = json.dumps({"sender_role": sender_role})
        self.client.send_channel_message(
            ChannelArn=channel_arn,
            Content=content,
            Persistence="PERSISTENT",
            Type="STANDARD",
            ChimeBearer=self.user_arn,
            Metadata=metadata,
        )

    def get_history(self, channel_arn: str) -> List[Dict[str, Any]]:
        """
        Завантажує всю історію повідомлень із каналу,
        повертає список у форматі [{role, content}, ...],
        читаючи роль із metadata кожного повідомлення.
        """
        messages: List[Dict[str, Any]] = []
        next_token = None

        while True:
            params: Dict[str, Any] = {
                "ChannelArn": channel_arn,
                "ChimeBearer": self.user_arn,
                "SortOrder": "ASCENDING",
                "MaxResults": 50,
            }
            if next_token:
                params["NextToken"] = next_token

            resp = self.client.list_channel_messages(**params)
            for m in resp.get("ChannelMessages", []):
                # парсимо metadata, щоб дізнатись роль відправника
                sender_role = "assistant"
                md_str = m.get("Metadata")
                if md_str:
                    try:
                        md = json.loads(md_str)
                        if md.get("sender_role") in ("user", "assistant"):
                            sender_role = md["sender_role"]
                    except json.JSONDecodeError:
                        pass

                messages.append({
                    "role": sender_role,
                    "content": m["Content"],
                })

            next_token = resp.get("NextToken")
            if not next_token:
                break

        return messages
