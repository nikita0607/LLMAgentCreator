from sqlalchemy import Column, Integer, ForeignKey, DateTime, func, String, Text, JSON
from sqlalchemy.orm import relationship
from app.db import Base

class Session(Base):
    __tablename__ = "session"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agent.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    status = Column(String, default="active")
    current_node = Column(String, nullable=True)   # <-- новое поле
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    conversation_id = Column(String, nullable=True)
    visited_nodes = Column(Text, default='[]', nullable=True)  # JSON array of visited node IDs
    last_user_input = Column(JSON, nullable=True)  # Store last user input for nodes that need it

    agent = relationship("Agent", backref="sessions")
    user = relationship("User", backref="sessions")