import io
import tempfile
import os
from sqlalchemy.orm import Session
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader

from app.models.knowledge_base import KnowledgeNode, KnowledgeEmbedding
import numpy as np


class KnowledgeService:
    def __init__(self, db: Session):
        self.db = db
        self.embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )


    def _load_document(self, file: io.BytesIO, filename: str):
        """Сохраняем файл во временную директорию и подгружаем через лоадер"""
        suffix = os.path.splitext(filename)[-1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name

        try:
            if filename.endswith(".txt"):
                loader = TextLoader(tmp_path, encoding="utf-8")
            elif filename.endswith(".pdf"):
                loader = PyPDFLoader(tmp_path)
            elif filename.endswith(".docx"):
                loader = Docx2txtLoader(tmp_path)
            else:
                raise ValueError("Unsupported file type")

            docs = loader.load()
        finally:
            os.remove(tmp_path)

        return docs

    def add_document(self, agent_id: int, node_id: str, file: io.BytesIO, filename: str):
        """Загрузка документа, создание KnowledgeNode (если надо) и эмбеддингов"""

        # 1. Загружаем текст
        docs = self._load_document(file, filename)
        full_text = "\n".join([d.page_content for d in docs])

        # 2. Проверяем / создаём KnowledgeNode
        kb_node = (
            self.db.query(KnowledgeNode)
            .filter(KnowledgeNode.agent_id == agent_id, KnowledgeNode.node_id == node_id)
            .first()
        )
        if not kb_node:
            kb_node = KnowledgeNode(
                agent_id=agent_id,
                node_id=node_id,  # UI id
                name=filename,
                source_type="file"
            )
            self.db.add(kb_node)
            self.db.commit()
            self.db.refresh(kb_node)  # ✅ теперь kb_node.id доступен

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_text(full_text)

        # 4. Создаем эмбеддинги
        vectors = self.embeddings_model.embed_documents(chunks)

        # 5. Сохраняем чанки в knowledge_embeddings
        embeddings_to_add = [
            KnowledgeEmbedding(
                kb_id=kb_node.id,
                chunk_index=idx,
                embedding=vector,
                text_chunk=chunk
            )
            for idx, (chunk, vector) in enumerate(zip(chunks, vectors))
        ]

        self.db.bulk_save_objects(embeddings_to_add)
        self.db.commit()

        return kb_node

    def search_embeddings(self, agent_id: int, node_id: int, query: str, top_k: int = 5):
        # Проверяем ноду
        kb_node = (
            self.db.query(KnowledgeNode)
            .filter(KnowledgeNode.agent_id == agent_id, KnowledgeNode.node_id == node_id)
            .first()
        )
        if not kb_node:
            return []

        query_emb = self.embeddings_model.embed_query(query)

        results = []
        for emb in kb_node.embeddings:
            results.append(emb.text_chunk)

        results.sort(key=lambda x: x[2], reverse=True)
        return results[:top_k]
