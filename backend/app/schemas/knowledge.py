from pydantic import BaseModel
from typing import List
from datetime import datetime

# ---------- KnowledgeBase ----------

class KnowledgeBaseCreate(BaseModel):
    name: str
    type: str
    content: str

class KnowledgeBaseRead(BaseModel):
    id: int
    agent_id: int
    name: str
    type: str
    content: str
    created_at: datetime

    class Config:
        orm_mode = True


# ---------- KnowledgeEmbedding ----------

class KnowledgeEmbeddingCreate(BaseModel):
    kb_id: int
    chunk_index: int
    embedding: List[float]
    text_chunk: str

class KnowledgeEmbeddingRead(BaseModel):
    id: int
    kb_id: int
    chunk_index: int
    text_chunk: str

    class Config:
        orm_mode = True
