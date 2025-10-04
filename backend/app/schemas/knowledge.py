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


# Removed KnowledgeEmbedding schemas as we're no longer using embeddings