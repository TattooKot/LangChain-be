from sqlalchemy import create_engine, Column, String, DateTime, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker
import uuid, datetime

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

    def create_session(self) -> str:
        session = ChatSession()
        self.db.add(session)
        self.db.commit()
        return session.id

    def list_sessions(self) -> list[str]:
        return [s.id for s in self.db.query(ChatSession).all()]

    def delete_session(self, conv_id: str) -> None:
        obj = self.db.query(ChatSession).filter_by(id=conv_id).first()
        if obj:
            self.db.delete(obj)
            self.db.commit()
