import io
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.models.knowledge_base import KnowledgeNode, KnowledgeEmbedding
from app.services.data_extractors import DataExtractorFactory
from app.services.data_extractors.web_extractor import WebDataExtractor
import numpy as np


class KnowledgeService:
    def __init__(self, db: Session, groq_api_key: Optional[str] = None):
        self.db = db
        self.embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        # Инициализируем фабрику экстракторов
        self.extractor_factory = DataExtractorFactory(groq_api_key=groq_api_key)


    def add_source(self, agent_id: int, node_id: str, data: Any, source_name: str, 
                   source_metadata: Optional[Dict[str, Any]] = None):
        """
        Общий метод для добавления любого типа источника данных.
        
        Args:
            agent_id: ID агента
            node_id: ID ноды в UI
            data: Данные источника (файл, URL, и т.д.)
            source_name: Имя источника
            source_metadata: Дополнительные метаданные источника
            
        Returns:
            KnowledgeNode: Созданная или обновленная нода
        """
        try:
            # Создаем SourceInput
            source_input = self.extractor_factory.create_source_input(
                data=data,
                source_name=source_name,
                metadata=source_metadata or {}
            )
            
            # Проверяем, является ли источник веб-страницей
            web_extractor = WebDataExtractor()
            is_web_source = web_extractor.can_handle(source_input)
            
            if is_web_source:
                # Для веб-источников просто сохраняем URL без обработки
                kb_node = self._create_or_update_knowledge_node(
                    agent_id=agent_id,
                    node_id=node_id,
                    source_name=source_name,
                    source_type="web",
                    source_data={"url": data, **(source_metadata or {})},
                    extractor_metadata={"source_type": "web", "url": data}
                )
                # Для веб-источников не создаем embeddings
                return kb_node
            else:
                # Для других источников используем стандартную обработку
                extracted_data = self.extractor_factory.extract_from_source(
                    data=data,
                    source_name=source_name,
                    metadata=source_metadata
                )
                
                # Создаем или обновляем KnowledgeNode
                kb_node = self._create_or_update_knowledge_node(
                    agent_id=agent_id,
                    node_id=node_id,
                    source_name=source_name,
                    source_type=extracted_data.source_type,
                    source_data=source_metadata,
                    extractor_metadata=extracted_data.metadata
                )
                
                # Разбиваем текст на чанки и создаем embeddings
                self._create_embeddings_for_node(kb_node, extracted_data.text_content)
                
                return kb_node
            
        except Exception as e:
            raise Exception(f"Error adding source {source_name}: {str(e)}")

    def add_document(self, agent_id: int, node_id: str, file: io.BytesIO, filename: str):
        """
        Обратная совместимость для старого API.
        Использует новую архитектуру.
        """
        return self.add_source(
            agent_id=agent_id,
            node_id=node_id,
            data=file,
            source_name=filename,
            source_metadata={"upload_type": "file"}
        )

    def add_url(self, agent_id: int, node_id: str, url: str, url_metadata: Optional[Dict[str, Any]] = None):
        """
        Добавляет веб-страницу как источник знаний.
        
        Args:
            agent_id: ID агента
            node_id: ID ноды в UI
            url: URL веб-страницы
            url_metadata: Дополнительные метаданные
        """
        metadata = url_metadata or {}
        metadata.update({
            "url": url,
            "upload_type": "url"
        })
        
        return self.add_source(
            agent_id=agent_id,
            node_id=node_id,
            data=url,
            source_name=url,
            source_metadata=metadata
        )
    
    def add_audio(self, agent_id: int, node_id: str, audio_file: io.BytesIO, filename: str, 
                  audio_metadata: Optional[Dict[str, Any]] = None):
        """
        Добавляет аудио файл с транскрибацией.
        
        Args:
            agent_id: ID агента
            node_id: ID ноды в UI
            audio_file: Аудио файл
            filename: Имя файла
            audio_metadata: Дополнительные метаданные
        """
        metadata = audio_metadata or {}
        metadata.update({
            "filename": filename,
            "upload_type": "audio"
        })
        
        return self.add_source(
            agent_id=agent_id,
            node_id=node_id,
            data=audio_file,
            source_name=filename,
            source_metadata=metadata
        )
    
    def _create_or_update_knowledge_node(self, agent_id: int, node_id: str, source_name: str,
                                        source_type: str, source_data: Optional[Dict[str, Any]],
                                        extractor_metadata: Dict[str, Any]) -> KnowledgeNode:
        """
        Создает новую или обновляет существующую ноду знаний.
        """
        kb_node = (
            self.db.query(KnowledgeNode)
            .filter(KnowledgeNode.agent_id == agent_id, KnowledgeNode.node_id == node_id)
            .first()
        )
        
        if kb_node:
            # Обновляем существующую ноду
            kb_node.name = source_name
            kb_node.source_type = source_type
            kb_node.source_data = source_data
            kb_node.extractor_metadata = extractor_metadata
            
            # Удаляем старые embeddings только для не-веб источников
            if source_type != "web":
                self.db.query(KnowledgeEmbedding).filter(
                    KnowledgeEmbedding.kb_id == kb_node.id
                ).delete()
        else:
            # Создаем новую ноду
            kb_node = KnowledgeNode(
                agent_id=agent_id,
                node_id=node_id,
                name=source_name,
                source_type=source_type,
                source_data=source_data,
                extractor_metadata=extractor_metadata
            )
            self.db.add(kb_node)
        
        self.db.commit()
        self.db.refresh(kb_node)
        return kb_node
    
    def _create_embeddings_for_node(self, kb_node: KnowledgeNode, text_content: str):
        """
        Создает embeddings для текста.
        """
        # Разбиваем текст на чанки
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_text(text_content)
        
        if not chunks:
            return
        
        # Создаем embeddings
        vectors = self.embeddings_model.embed_documents(chunks)
        
        # Создаем объекты embeddings
        embeddings = [
            KnowledgeEmbedding(
                kb_id=kb_node.id,
                chunk_index=idx,
                embedding=vector,
                text_chunk=chunk
            )
            for idx, (chunk, vector) in enumerate(zip(chunks, vectors))
        ]
        
        # Сохраняем в базу
        self.db.add_all(embeddings)
        self.db.commit()
    
    def search_embeddings(self, agent_id: int, node_id: str, query: str, top_k: int = 5):
        """
        Поиск по embeddings в конкретной ноде.
        """
        kb_node = (
            self.db.query(KnowledgeNode)
            .filter(KnowledgeNode.agent_id == agent_id, KnowledgeNode.node_id == node_id)
            .first()
        )
        if not kb_node:
            return []

        query_emb = self.embeddings_model.embed_query(query)
        
        # Простой поиск по косинусному сходству
        results = []
        for emb in kb_node.embeddings:
            if emb.embedding is not None:
                # Вычисляем косинусное сходство
                similarity = np.dot(query_emb, emb.embedding) / (
                    np.linalg.norm(query_emb) * np.linalg.norm(emb.embedding)
                )
                results.append((emb.id, emb.text_chunk, float(similarity)))

        # Сортируем по сходству
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:top_k]
    
    def get_source_info(self, agent_id: int, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает информацию об источнике знаний.
        """
        kb_node = (
            self.db.query(KnowledgeNode)
            .filter(KnowledgeNode.agent_id == agent_id, KnowledgeNode.node_id == node_id)
            .first()
        )
        
        if not kb_node:
            return None
        
        return {
            "id": kb_node.id,
            "agent_id": kb_node.agent_id,
            "node_id": kb_node.node_id,
            "name": kb_node.name,
            "source_type": kb_node.source_type,
            "source_data": kb_node.source_data,
            "extractor_metadata": kb_node.extractor_metadata,
            "created_at": kb_node.created_at.isoformat() if kb_node.created_at else None,
            "updated_at": kb_node.updated_at.isoformat() if kb_node.updated_at else None,
            "embeddings_count": len(kb_node.embeddings)
        }
    
    def get_supported_source_types(self) -> Dict[str, List[str]]:
        """
        Возвращает список поддерживаемых типов источников.
        """
        return self.extractor_factory.get_all_supported_types()
    
    def scrape_and_search_web_source(self, agent_id: int, node_id: str, query: str, top_k: int = 5):
        """
        Выполняет реальный скрапинг веб-страницы и поиск по извлеченному контенту.
        
        Args:
            agent_id: ID агента
            node_id: ID ноды
            query: Поисковый запрос
            top_k: Количество результатов
            
        Returns:
            Список результатов поиска
        """
        # Получаем информацию о веб-источнике
        kb_node = (
            self.db.query(KnowledgeNode)
            .filter(
                KnowledgeNode.agent_id == agent_id,
                KnowledgeNode.node_id == node_id,
                KnowledgeNode.source_type == "web"
            )
            .first()
        )
        
        if not kb_node or not kb_node.source_data or "url" not in kb_node.source_data:
            return []
        
        url = kb_node.source_data["url"]
        
        try:
            # Выполняем реальный скрапинг
            web_extractor = WebDataExtractor()
            source_input = self.extractor_factory.create_source_input(url, url, {})
            extracted_data = web_extractor.extract(source_input)

            print(extracted_data)
            
            # Разбиваем текст на чанки для поиска
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = splitter.split_text(extracted_data.text_content)

            print(chunks)
            
            if not chunks:
                return []
            
            # Создаем embeddings для извлеченного текста
            query_emb = self.embeddings_model.embed_query(query)
            chunk_vectors = self.embeddings_model.embed_documents(chunks)
            
            # Поиск по косинусному сходству
            results = []
            for idx, (chunk, vector) in enumerate(zip(chunks, chunk_vectors)):
                # Вычисляем косинусное сходство
                similarity = np.dot(query_emb, vector) / (
                    np.linalg.norm(query_emb) * np.linalg.norm(vector)
                )
                results.append((idx, chunk, float(similarity)))

            # Сортируем по сходству
            results.sort(key=lambda x: x[2], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            print(f"Error scraping web source: {str(e)}")
            return []