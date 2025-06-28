import os
from dotenv import load_dotenv

# Завантажує .env, якщо він присутній
load_dotenv()

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")

settings = Settings()