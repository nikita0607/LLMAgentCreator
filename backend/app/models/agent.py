from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db import Base

class Agent(Base):
    __tablename__ = "agent"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    system_prompt = Column(String, nullable=False)
    voice_id = Column(String, nullable=False)  # ElevenLabs voice
    logic = Column(JSON, nullable=True)        # drag&drop flow (JSON)
    owner_id = Column(Integer, ForeignKey("user.id"))

    owner = relationship("User", backref="agents")
