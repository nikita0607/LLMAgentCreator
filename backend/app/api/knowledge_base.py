import io
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from app.db import get_db
from app.models.agent import Agent
from app.models.knowledge_base import KnowledgeNode
from app.services.knowledge_service import KnowledgeService
from app.core.config import settings

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
    source_data: Optional[dict] = None
    extractor_metadata: Optional[dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    embeddings_count: int = 0


class UrlSourceRequest(BaseModel):
    url: HttpUrl
    description: Optional[str] = None


class SupportedTypesResponse(BaseModel):
    supported_types: dict


@router.post("/upload/{agent_id}/{node_id}")
async def upload_knowledge_file(agent_id: int, node_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Загрузка файла в ноду знаний"""
    # Получаем GROQ API key из настроек для аудио транскрибации
    groq_api_key = getattr(settings, 'GROQ_API_KEY', None)
    service = KnowledgeService(db, groq_api_key=groq_api_key)
    
    content = await file.read()
    
    try:
        kb_node = service.add_source(
            agent_id=agent_id,
            node_id=node_id,
            data=io.BytesIO(content),
            source_name=file.filename,
            source_metadata={
                "content_type": file.content_type,
                "file_size": len(content)
            }
        )
        
        return {
            "status": "ok",
            "knowledge_node_id": kb_node.id,
            "filename": kb_node.name,
            "source_type": kb_node.source_type
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.post("/url/{agent_id}/{node_id}")
def add_url_source(agent_id: int, node_id: str, url_request: UrlSourceRequest, db: Session = Depends(get_db)):
    """Добавление URL как источника знаний"""
    groq_api_key = getattr(settings, 'GROQ_API_KEY', None)
    service = KnowledgeService(db, groq_api_key=groq_api_key)
    
    try:
        kb_node = service.add_url(
            agent_id=agent_id,
            node_id=node_id,
            url=str(url_request.url),
            url_metadata={
                "description": url_request.description
            }
        )
        
        return {
            "status": "ok",
            "knowledge_node_id": kb_node.id,
            "url": str(url_request.url),
            "source_type": kb_node.source_type
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/audio/{agent_id}/{node_id}")
async def upload_audio_file(agent_id: int, node_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Загрузка аудио файла для транскрибации"""
    groq_api_key = getattr(settings, 'GROQ_API_KEY', None)
    if not groq_api_key:
        raise HTTPException(status_code=501, detail="Audio transcription not configured (missing GROQ_API_KEY)")
    
    service = KnowledgeService(db, groq_api_key=groq_api_key)
    
    content = await file.read()
    
    try:
        kb_node = service.add_audio(
            agent_id=agent_id,
            node_id=node_id,
            audio_file=io.BytesIO(content),
            filename=file.filename,
            audio_metadata={
                "content_type": file.content_type,
                "file_size": len(content)
            }
        )
        
        return {
            "status": "ok",
            "knowledge_node_id": kb_node.id,
            "filename": kb_node.name,
            "source_type": kb_node.source_type
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/info/{agent_id}/{node_id}", response_model=KnowledgeNodeInfo | None)
def get_knowledge_info(agent_id: int, node_id: str, db: Session = Depends(get_db)):
    """Получение информации о ноде знаний"""
    groq_api_key = getattr(settings, 'GROQ_API_KEY', None)
    service = KnowledgeService(db, groq_api_key=groq_api_key)
    
    info = service.get_source_info(agent_id, node_id)
    
    if not info:
        return None
    
    return KnowledgeNodeInfo(**info)


@router.post("/search/{agent_id}/{node_id}", response_model=list[KnowledgeSearchResult])
def search_knowledge(agent_id: int, node_id: str, request: KnowledgeSearchRequest, db: Session = Depends(get_db)):
    """Поиск по ноде знаний"""
    groq_api_key = getattr(settings, 'GROQ_API_KEY', None)
    service = KnowledgeService(db, groq_api_key=groq_api_key)
    
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


@router.get("/supported-types", response_model=SupportedTypesResponse)
def get_supported_source_types(db: Session = Depends(get_db)):
    """Получение списка поддерживаемых типов источников"""
    groq_api_key = getattr(settings, 'GROQ_API_KEY', None)
    service = KnowledgeService(db, groq_api_key=groq_api_key)
    
    supported_types = service.get_supported_source_types()
    
    return SupportedTypesResponse(supported_types=supported_types)
