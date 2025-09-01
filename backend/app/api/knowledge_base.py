import io

from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.agent import Agent
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


class KnowledgeSearchRequest(BaseModel):
    agent_id: int
    query: str
    top_k: int = 5


class KnowledgeSearchResult(BaseModel):
    embedding_id: int
    text_chunk: str
    score: float


@router.post("/upload", response_model=dict)
async def upload_document(agent_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    content = await file.read()
    kb = service.add_document(agent_id=agent_id, file=io.BytesIO(content), filename=file.filename)

    return {
        "status": "success",
        "knowledge_base_id": kb.id,
        "filename": kb.name,
        "chunks": len(kb.embeddings),
    }


@router.post("/search", response_model=list[KnowledgeSearchResult])
def search_knowledge(request: KnowledgeSearchRequest, db: Session = Depends(get_db)):
    # Проверяем агента
    agent = db.query(Agent).filter(Agent.id == request.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    service = KnowledgeService(db)
    results = service.search_embeddings(request.agent_id, request.query, top_k=request.top_k)

    return [
        KnowledgeSearchResult(
            embedding_id=id,
            text_chunk=text,
            score=score
        )
        for id, text, score in results
    ]
