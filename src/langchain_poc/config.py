from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field

load_dotenv()

class Settings(BaseSettings):
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")

    # Postgres для зберігання списку сесій
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # Chime SDK для зберігання самих повідомлень
    AWS_REGION: str = Field("us-east-1", env="AWS_REGION")
    CHIME_APP_INSTANCE_ARN: str = Field(..., env="AWS_CHIME_APP_INSTANCE_ARN")
    CHIME_APP_INSTANCE_USER_ARN: str = Field(..., env="AWS_CHIME_APP_INSTANCE_USER_ARN")

settings = Settings()
