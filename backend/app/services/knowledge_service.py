import io
import tempfile
import os
from sqlalchemy.orm import Session
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader

from app.models.knowledge_base import KnowledgeBase, KnowledgeEmbedding
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
            os.remove(tmp_path)  # очищаем tmp-файл

        return docs

    def add_document(self, agent_id: int, file: io.BytesIO, filename: str) -> KnowledgeBase:
        """Загрузка документа, создание базы знаний и эмбеддингов"""

        # 1. Загружаем текст
        docs = self._load_document(file, filename)
        full_text = "\n".join([d.page_content for d in docs])

        # 2. Создаем запись в knowledge_base
        kb = KnowledgeBase(
            agent_id=agent_id,
            name=filename,
            type=filename.split(".")[-1],
            content=full_text
        )
        self.db.add(kb)
        self.db.commit()
        self.db.refresh(kb)

        # 3. Разбиваем текст на чанки
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_text(full_text)

        # 4. Создаем эмбеддинги
        vectors = self.embeddings_model.embed_documents(chunks)

        # 5. Сохраняем чанки в knowledge_embeddings
        for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
            emb = KnowledgeEmbedding(
                kb_id=kb.id,
                chunk_index=idx,
                embedding=vector,
                text_chunk=chunk
            )
            self.db.add(emb)

        self.db.commit()
        return kb

    def search_embeddings(self, agent_id: int, query: str, top_k: int = 5):
        """Поиск по эмбеддингам базы знаний"""

        # Получаем все эмбеддинги агента
        embeddings_list = (
            self.db.query(KnowledgeEmbedding)
            .join(KnowledgeBase)
            .filter(KnowledgeBase.agent_id == agent_id)
            .all()
        )

        if not embeddings_list:
            return []

        # Генерируем embedding запроса
        query_vector = self.embeddings_model.embed_query(query)

        # Косинусное сходство
        def cosine_sim(a, b):
            a = np.array(a)
            b = np.array(b)
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

        scored = [
            (emb.id, emb.text_chunk, cosine_sim(query_vector, emb.embedding))
            for emb in embeddings_list
        ]

        # Сортируем и берем top_k
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:top_k]