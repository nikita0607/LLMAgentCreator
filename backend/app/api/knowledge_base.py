import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db import get_db
from app.models.agent import Agent
from app.models.knowledge_base import KnowledgeNode
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


class KnowledgeSearchRequest(BaseModel):
    query: str
    top_k: int = 5


class KnowledgeSearchResult(BaseModel):
    embedding_id: int
    text_chunk: str
    score: float


class KnowledgeNodeInfo(BaseModel):
    id: int
    agent_id: int
    node_id: str
    name: str
    source_type: str
    created_at: str


@router.post("/upload/{agent_id}/{node_id}")
async def upload_knowledge_file(agent_id: int, node_id: str, file: UploadFile = File(...),  db: Session = Depends(get_db)):
    print(agent_id)
    print(node_id)
    service = KnowledgeService(db)
    content = await file.read()

    kb_node = service.add_document(
        agent_id=agent_id,
        node_id=node_id,
        file=io.BytesIO(content),
        filename=file.filename
    )

    return {
        "status": "ok",
        "knowledge_node_id": kb_node.id,
        "filename": kb_node.name
    }


@router.post("/search/{agent_id}/{node_id}", response_model=list[KnowledgeSearchResult])
def search_knowledge(agent_id: int, node_id: int, request: KnowledgeSearchRequest, db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    results = service.search_embeddings(
        agent_id=agent_id,
        node_id=node_id,
        query=request.query,
        top_k=request.top_k,
    )

    return [
        KnowledgeSearchResult(
            embedding_id=emb_id,
            text_chunk=text,
            score=score,
        )
        for emb_id, text, score in results
    ]


@router.get("/info/{agent_id}/{node_id}", response_model=KnowledgeNodeInfo | None)
def get_knowledge_info(agent_id: int, node_id: str, db: Session = Depends(get_db)):
    """Get knowledge node information including filename"""
    kb_node = (
        db.query(KnowledgeNode)
        .filter(KnowledgeNode.agent_id == agent_id, KnowledgeNode.node_id == node_id)
        .first()
    )
    
    if not kb_node:
        return None
    
    return KnowledgeNodeInfo(
        id=kb_node.id,
        agent_id=kb_node.agent_id,
        node_id=kb_node.node_id,
        name=kb_node.name,
        source_type=kb_node.source_type,
        created_at=kb_node.created_at.isoformat() if kb_node.created_at else ""
    )
