from sqlalchemy import Column, Integer, ForeignKey, DateTime, func, String, JSON
from sqlalchemy.orm import relationship
from app.db import Base

class SessionMessage(Base):
    __tablename__ = "session_message"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("session.id"), nullable=False)
    sender = Column(String, nullable=False)  # "user" или "agent"
    text = Column(String, nullable=False)
    action = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", backref="messages")