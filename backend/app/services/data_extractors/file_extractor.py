import io
import os
import tempfile
from typing import Dict, Any, List
from datetime import datetime

from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader

from .base import DataExtractor, SourceInput, ExtractedData


class FileDataExtractor(DataExtractor):
    """
    Экстрактор для обработки файлов различных форматов.
    Поддерживает: TXT, PDF, DOCX
    """
    
    SUPPORTED_EXTENSIONS = {
        '.txt': 'text',
        '.pdf': 'pdf', 
        '.docx': 'docx',
        '.doc': 'doc'
    }
    
    def can_handle(self, source_input: SourceInput) -> bool:
        """Проверяет, может ли обработать файл по расширению"""
        if not isinstance(source_input.data, (io.BytesIO, bytes)):
            return False
            
        # Проверяем расширение файла
        _, ext = os.path.splitext(source_input.source_name.lower())
        return ext in self.SUPPORTED_EXTENSIONS
    
    def get_supported_types(self) -> List[str]:
        """Возвращает список поддерживаемых типов файлов"""
        return list(self.SUPPORTED_EXTENSIONS.values())
    
    def extract(self, source_input: SourceInput) -> ExtractedData:
        """Извлекает текст из файла"""
        self.validate_input(source_input)
        
        if not self.can_handle(source_input):
            raise ValueError(f"Unsupported file type for {source_input.source_name}")
        
        # Получаем расширение файла
        _, ext = os.path.splitext(source_input.source_name.lower())
        file_type = self.SUPPORTED_EXTENSIONS[ext]
        
        try:
            # Загружаем документ через langchain
            docs = self._load_document_with_langchain(source_input.data, source_input.source_name)
            
            # Объединяем все страницы в один текст
            full_text = "\n".join([doc.page_content for doc in docs])
            
            # Предварительная обработка текста
            processed_text = self.preprocess_text(full_text)
            
            # Создаем метаданные
            metadata = self.get_default_metadata(source_input)
            metadata.update({
                "file_type": file_type,
                "file_extension": ext,
                "file_size": len(source_input.data.getvalue()) if hasattr(source_input.data, 'getvalue') else None,
                "pages_count": len(docs),
                "processed_at": datetime.now().isoformat()
            })
            
            return ExtractedData(
                text_content=processed_text,
                metadata=metadata,
                source_type="file"
            )
            
        except Exception as e:
            raise Exception(f"Error extracting text from file {source_input.source_name}: {str(e)}")
    
    def _load_document_with_langchain(self, file_data: io.BytesIO, filename: str):
        """Загружает документ используя соответствующий langchain loader"""
        _, ext = os.path.splitext(filename.lower())
        
        # Сохраняем файл во временную директорию
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            if isinstance(file_data, io.BytesIO):
                tmp.write(file_data.getvalue())
            else:
                tmp.write(file_data)
            tmp_path = tmp.name
        
        try:
            # Выбираем подходящий loader
            if ext == '.txt':
                loader = TextLoader(tmp_path, encoding="utf-8")
            elif ext == '.pdf':
                loader = PyPDFLoader(tmp_path)
            elif ext in ['.docx', '.doc']:
                loader = Docx2txtLoader(tmp_path)
            else:
                raise ValueError(f"Unsupported file extension: {ext}")
            
            # Загружаем документ
            docs = loader.load()
            return docs
            
        finally:
            # Удаляем временный файл
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def validate_input(self, source_input: SourceInput) -> bool:
        """Дополнительная валидация для файлов"""
        super().validate_input(source_input)
        
        if not isinstance(source_input.data, (io.BytesIO, bytes)):
            raise ValueError("File data must be BytesIO or bytes")
        
        if not source_input.source_name:
            raise ValueError("Filename is required")
            
        # Проверяем, что файл не пустой
        if isinstance(source_input.data, io.BytesIO):
            if source_input.data.getvalue() == b'':
                raise ValueError("File is empty")
        elif isinstance(source_input.data, bytes):
            if len(source_input.data) == 0:
                raise ValueError("File is empty")
        
        return True
    
    def preprocess_text(self, text: str) -> str:
        """Специализированная обработка текста для файлов"""
        # Базовая обработка
        text = super().preprocess_text(text)
        
        # Дополнительная обработка для файлов
        # Удаляем лишние пробелы
        text = ' '.join(text.split())
        
        # Восстанавливаем переносы строк для абзацев
        text = text.replace('. ', '.\n')
        
        return text