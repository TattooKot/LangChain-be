import uuid
import datetime
from typing import List, Optional
from sqlalchemy import (
    create_engine,
    Column,
    String,
    DateTime,
    MetaData,
)
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

engine = create_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base(metadata=MetaData())

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    # наш internal ID
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # ARN каналу Chime
    channel_arn = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# створюємо таблицю, якщо її ще нема
Base.metadata.create_all(bind=engine)

class SessionRepository:
    def __init__(self):
        self.db = SessionLocal()

    def create(self, channel_arn: str) -> str:
        """
        Створює новий запис із згенерованим session_id і існуючим channel_arn.
        Повертає session_id.
        """
        sess = ChatSession(channel_arn=channel_arn)
        self.db.add(sess)
        self.db.commit()
        return sess.id

    def list(self) -> List[dict]:
        """
        Повертає список об’єктів { id, channel_arn }.
        """
        return [
            {"id": row.id, "channel_arn": row.channel_arn}
            for row in self.db.query(ChatSession).all()
        ]

    def get_channel_arn(self, session_id: str) -> Optional[str]:
        """
        За session_id повертає відповідний channel_arn або None.
        """
        row = (
            self.db.query(ChatSession)
            .filter_by(id=session_id)
            .first()
        )
        return row.channel_arn if row else None

    def delete(self, session_id: str) -> None:
        obj = self.db.query(ChatSession).filter_by(id=session_id).first()
        if obj:
            self.db.delete(obj)
            self.db.commit()
