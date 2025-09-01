from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agent.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # pdf, docx, txt
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    embeddings = relationship("KnowledgeEmbedding", back_populates="knowledge_base")


class KnowledgeEmbedding(Base):
    __tablename__ = "knowledge_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    kb_id = Column(Integer, ForeignKey("knowledge_base.id", ondelete="CASCADE"))
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(384))  # ✅ теперь 384
    text_chunk = Column(Text, nullable=False)

    knowledge_base = relationship("KnowledgeBase", back_populates="embeddings")
