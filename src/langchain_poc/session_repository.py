import uuid
import datetime
from typing import List
from sqlalchemy import create_engine, Column, String, DateTime, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

engine = create_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base(metadata=MetaData())

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

class SessionRepository:
    def __init__(self):
        self.db = SessionLocal()

    def create(self) -> str:
        sess = ChatSession()
        self.db.add(sess)
        self.db.commit()
        return sess.id

    def list(self) -> List[str]:
        return [row.id for row in self.db.query(ChatSession).all()]

    def delete(self, session_id: str) -> None:
        obj = self.db.query(ChatSession).filter_by(id=session_id).first()
        if obj:
            self.db.delete(obj)
            self.db.commit()
