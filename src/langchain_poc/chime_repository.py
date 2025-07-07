# src/langchain_poc/chime_repository.py

import json
import boto3
import uuid
import urllib.parse
from datetime import datetime, timezone
import hashlib
import hmac
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

    def send_initial_message(self, channel_arn: str, content: str) -> str:
        """
        Sends an initial message to the channel and returns the MessageId.
        This MessageId will be used for subsequent updates.
        """
        metadata = json.dumps({"sender_role": "assistant"})
        resp = self.client.send_channel_message(
            ChannelArn=channel_arn,
            Content=content,
            Persistence="PERSISTENT",
            Type="STANDARD",
            ChimeBearer=self.user_arn,
            Metadata=metadata,
        )
        return resp["MessageId"]

    def update_channel_message(self, channel_arn: str, message_id: str, content: str) -> None:
        """
        Updates an existing channel message with new content.
        This is used to update the "Thinking..." message with streaming AI response.
        """
        metadata = json.dumps({"sender_role": "assistant"})
        self.client.update_channel_message(
            ChannelArn=channel_arn,
            MessageId=message_id,
            Content=content,
            ChimeBearer=self.user_arn,
            Metadata=metadata,
        )

    def get_websocket_url(self) -> str:
        """
        Get the AWS Chime WebSocket URL for real-time messaging with proper AWS Signature V4.
        This URL can be used by the frontend to connect directly to AWS Chime.
        """
        # Get the messaging session endpoint
        response = self.client.get_messaging_session_endpoint()
        endpoint_url = response["Endpoint"]["Url"]
        
        # The endpoint URL from AWS is just the host without protocol
        # It should be in format: node001.ue1.ws-messaging.chime.aws
        if endpoint_url and "ws-messaging.chime.aws" in endpoint_url:
            host = endpoint_url
        else:
            # Parse the endpoint URL to get the host (fallback)
            parsed = urllib.parse.urlparse(endpoint_url)
            host = parsed.netloc
            
            # If host is empty, construct it manually based on region
            if not host:
                # Fallback to standard format
                host = f"messaging-chime.{settings.AWS_REGION}.amazonaws.com"
        
        # Get AWS credentials from the boto3 session
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if not credentials:
            raise Exception("AWS credentials not found")
        
        # Generate required parameters
        session_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)
        datestamp = timestamp.strftime('%Y%m%d')
        amzdate = timestamp.strftime('%Y%m%dT%H%M%SZ')
        
        # Create the canonical request
        method = 'GET'
        canonical_uri = '/connect'
        
        # Query parameters (must be URL encoded)
        query_params = {
            'X-Amz-Algorithm': 'AWS4-HMAC-SHA256',
            'X-Amz-Credential': f"{credentials.access_key}/{datestamp}/{settings.AWS_REGION}/chime/aws4_request",
            'X-Amz-Date': amzdate,
            'X-Amz-Expires': '300',  # 5 minutes
            'X-Amz-SignedHeaders': 'host',
            'sessionId': session_id,
            'userArn': self.user_arn,
        }
        
        # Add security token if present (for temporary credentials)
        if credentials.token:
            query_params['X-Amz-Security-Token'] = credentials.token
        
        # Sort and encode query parameters
        canonical_querystring = '&'.join([
            f"{urllib.parse.quote_plus(k)}={urllib.parse.quote_plus(str(v))}"
            for k, v in sorted(query_params.items())
        ])
        
        # Create canonical headers
        canonical_headers = f'host:{host}\n'
        signed_headers = 'host'
        
        # Create payload hash (empty for GET request)
        payload_hash = hashlib.sha256(b'').hexdigest()
        
        # Create canonical request
        canonical_request = f"{method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
        
        # Create string to sign
        algorithm = 'AWS4-HMAC-SHA256'
        credential_scope = f"{datestamp}/{settings.AWS_REGION}/chime/aws4_request"
        string_to_sign = f"{algorithm}\n{amzdate}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"
        
        # Calculate signature
        def sign(key, msg):
            return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
        
        def getSignatureKey(key, dateStamp, regionName, serviceName):
            kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
            kRegion = sign(kDate, regionName)
            kService = sign(kRegion, serviceName)
            kSigning = sign(kService, 'aws4_request')
            return kSigning
        
        signing_key = getSignatureKey(credentials.secret_key, datestamp, settings.AWS_REGION, 'chime')
        signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
        
        # Add signature to query parameters
        query_params['X-Amz-Signature'] = signature
        
        # Rebuild the canonical query string with signature
        final_querystring = '&'.join([
            f"{urllib.parse.quote_plus(k)}={urllib.parse.quote_plus(str(v))}"
            for k, v in sorted(query_params.items())
        ])
        
        # Convert to WebSocket URL
        websocket_url = f"wss://{host}{canonical_uri}?{final_querystring}"
        
        return websocket_url

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
                    "message_id": m.get("MessageId"),  # Include MessageId for potential updates
                })

            next_token = resp.get("NextToken")
            if not next_token:
                break

        return messages
