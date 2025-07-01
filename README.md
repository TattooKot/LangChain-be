
# LangChain PoC Backend

## Overview

This FastAPI-based backend provides:

- Session management via PostgreSQL.
- Messaging transport via AWS Chime SDK Messaging.
- Chat streaming with LangChain and OpenAI models.
- SSE (Server-Sent Events) endpoint for real-time streaming.

## Prerequisites

- Python 3.11+
- Poetry or pip
- PostgreSQL database
- AWS account with Chime SDK Messaging permissions
- AWS CLI configured with appropriate credentials

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/langchain-poc.git
   cd langchain-poc
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in a `.env` file:
   ```ini
   DATABASE_URL=postgresql://user:password@localhost/dbname
   OPENAI_API_KEY=your_openai_api_key
   AWS_REGION=us-east-1

   # From AWS Chime setup:
   CHIME_APP_INSTANCE_ARN=arn:aws:chime:us-east-1:123456789012:app-instance/abcdef12-3456-7890-abcd-ef1234567890
   CHIME_APP_INSTANCE_USER_ARN=arn:aws:chime:us-east-1:123456789012:app-instance/abcdef12-3456-7890-abcd-ef1234567890/user/YourUserId
   ```

## AWS Chime SDK Setup

Use the AWS CLI to create an AppInstance and AppInstanceUser:

```bash
# 1) Create AppInstance
aws chime create-app-instance \
  --cli-input-json '{
    "Name": "MyAppInstance",
    "Metadata": "LangChain PoC instance"
  }'
```
> **Note**: The response will include an `AppInstanceArn`. Example:
> ```json
> {
>   "AppInstanceArn": "arn:aws:chime:us-east-1:123456789012:app-instance/abcdef12-3456-7890-abcd-ef1234567890"
> }
> ```

```bash
# 2) Create AppInstanceUser
aws chime create-app-instance-user \
  --app-instance-arn arn:aws:chime:us-east-1:123456789012:app-instance/abcdef12-3456-7890-abcd-ef1234567890 \
  --app-instance-user-id "MyAppUser" \
  --name "LangChainUser" \
  --metadata "User for LangChain PoC"
```
> **Note**: The response will include an `AppInstanceUserArn`. Example:
> ```json
> {
>   "AppInstanceUserArn": "arn:aws:chime:us-east-1:123456789012:app-instance/abcdef12-3456-7890-abcd-ef1234567890/user/MyAppUser"
> }
> ```

Copy these ARNs into your `.env` file.

## Running the Server

```bash
uvicorn langchain_poc.api:app --reload
```

The API will be available at `http://localhost:8000`.

## Endpoints

- **GET** `/sessions`  
  List all chat sessions.

- **DELETE** `/sessions/{session_id}`  
  Delete a chat session.

- **POST** `/chime/stream-chat`  
  Stream chat via SSE.  
  Request body:  
  ```json
  {
    "message": "Hello",
    "conversation_id": "optional-internal-session-id"
  }
  ```

- **GET** `/chime/history/{session_id}`  
  Fetch full chat history for a session.

## Environment Variables

- `DATABASE_URL`  
- `OPENAI_API_KEY`  
- `AWS_REGION`  
- `CHIME_APP_INSTANCE_ARN`  
- `CHIME_APP_INSTANCE_USER_ARN`

## License

MIT
