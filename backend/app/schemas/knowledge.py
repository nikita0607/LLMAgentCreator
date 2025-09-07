from pydantic import BaseModel
from typing import List
from datetime import datetime


# ---------- KnowledgeNode ----------
class KnowledgeNodeCreate(BaseModel):
    agent_id: int
    node_id: str
    name: str
    source_type: str


class KnowledgeNodeRead(BaseModel):
    id: int
    agent_id: int
    node_id: str
    name: str
    source_type: str
    created_at: datetime

    class Config:
        orm_mode = True


# ---------- KnowledgeEmbedding ----------
class KnowledgeEmbeddingCreate(BaseModel):
    node_id: str
    chunk_index: int
    embedding: List[float]
    text_chunk: str


class KnowledgeEmbeddingRead(BaseModel):
    id: int
    node_id: str
    chunk_index: int
    text_chunk: str

    class Config:
        orm_mode = True
