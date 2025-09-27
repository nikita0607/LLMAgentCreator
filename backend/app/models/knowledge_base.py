from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, func, JSON
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db import Base


class KnowledgeNode(Base):
    __tablename__ = "knowledge_node"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agent.id", ondelete="CASCADE"))
    node_id = Column(String, nullable=False)  # id ноды из конструктора (UI)
    name = Column(String, nullable=False)     # удобное имя
    source_type = Column(String, nullable=False)  # file, web, audio, api и т.д.
    source_data = Column(JSON, nullable=True)  # Дополнительные метаданные источника
    extractor_metadata = Column(JSON, nullable=True)  # Метаданные от экстрактора
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    embeddings = relationship("KnowledgeEmbedding", back_populates="knowledge_node", cascade="all, delete-orphan")


class KnowledgeEmbedding(Base):
    __tablename__ = "knowledge_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    kb_id = Column(Integer, ForeignKey("knowledge_node.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(384))
    text_chunk = Column(Text, nullable=False)

    knowledge_node = relationship("KnowledgeNode", back_populates="embeddings")