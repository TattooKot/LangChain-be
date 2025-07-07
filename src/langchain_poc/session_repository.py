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

# --- SQLAlchemy setup ---
engine = create_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base(metadata=MetaData())


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    # internal session_id (ми його генеруємо зовні, тому тут не ставимо default)
    id = Column(String, primary_key=True, nullable=False)
    # ARN каналу Chime
    channel_arn = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# створюємо таблицю, якщо її ще немає
Base.metadata.create_all(bind=engine)


class SessionRepository:
    def __init__(self):
        self.db = SessionLocal()

    def create(self, session_id: str, channel_arn: str) -> None:
        """
        Створює запис із переданим session_id і channel_arn.
        """
        sess = ChatSession(id=session_id, channel_arn=channel_arn)
        self.db.add(sess)
        self.db.commit()

    def create_session(self, session_id: str, channel_arn: str) -> None:
        """
        Alias for create method to match the interface used in chat_service.
        """
        self.create(session_id, channel_arn)

    def list(self) -> List[dict]:
        """
        Повертає список об’єктів { id, channel_arn }.
        """
        rows = self.db.query(ChatSession).order_by(ChatSession.created_at).all()
        return [{"id": r.id, "channel_arn": r.channel_arn} for r in rows]

    def get_channel_arn(self, session_id: str) -> Optional[str]:
        """
        За session_id повертає відповідний channel_arn або None.
        """
        row = self.db.query(ChatSession).filter_by(id=session_id).first()
        return row.channel_arn if row else None

    def delete(self, session_id: str) -> None:
        """
        Видаляє запис за session_id.
        """
        obj = self.db.query(ChatSession).filter_by(id=session_id).first()
        if obj:
            self.db.delete(obj)
            self.db.commit()
