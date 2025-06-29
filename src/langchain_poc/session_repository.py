import uuid
import datetime
from typing import List
from sqlalchemy import (create_engine, Column, String, DateTime, MetaData)
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# 1) Налаштовуємо SQLAlchemy
engine = create_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base(metadata=MetaData())

# 2) Опис моделі chat_sessions
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# 3) Створюємо таблиці на стартапі
Base.metadata.create_all(bind=engine)

# 4) Репозиторій
class SessionRepository:
    def __init__(self):
        self.db = SessionLocal()

    def create_session(self) -> str:
        session = ChatSession()
        self.db.add(session)
        self.db.commit()
        return session.id

    def list_sessions(self) -> List[str]:
        return [s.id for s in self.db.query(ChatSession).all()]
