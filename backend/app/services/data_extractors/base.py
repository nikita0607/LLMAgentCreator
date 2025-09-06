from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import io


@dataclass
class ExtractedData:
    """Результат извлечения данных из источника"""
    text_content: str
    metadata: Dict[str, Any]
    source_type: str
    chunks: Optional[List[str]] = None  # Предварительно разбитый на чанки текст


@dataclass
class SourceInput:
    """Входные данные для извлечения"""
    data: Any  # Может быть файл, URL, или другие данные
    metadata: Dict[str, Any]  # Дополнительная информация о источнике
    source_name: str  # Имя источника (например, имя файла)


class DataExtractor(ABC):
    """
    Абстрактный базовый класс для извлечения текста из различных источников данных.
    
    Каждый конкретный экстрактор должен реализовать методы для:
    - Определения поддерживаемых типов источников
    - Извлечения текста из источника
    - Валидации входных данных
    """
    
    @abstractmethod
    def can_handle(self, source_input: SourceInput) -> bool:
        """
        Определяет, может ли данный экстрактор обработать источник.
        
        Args:
            source_input: Входные данные источника
            
        Returns:
            True, если экстрактор может обработать данный источник
        """
        pass
    
    @abstractmethod
    def extract(self, source_input: SourceInput) -> ExtractedData:
        """
        Извлекает текст из источника.
        
        Args:
            source_input: Входные данные источника
            
        Returns:
            ExtractedData с извлеченным текстом и метаданными
            
        Raises:
            ValueError: Если источник не может быть обработан
            Exception: Другие ошибки при извлечении
        """
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """
        Возвращает список поддерживаемых типов источников.
        
        Returns:
            Список строк с типами источников (например, ['file', 'pdf', 'docx'])
        """
        pass
    
    def validate_input(self, source_input: SourceInput) -> bool:
        """
        Валидирует входные данные.
        
        Args:
            source_input: Входные данные для валидации
            
        Returns:
            True, если данные валидны
            
        Raises:
            ValueError: Если данные невалидны
        """
        if not source_input.source_name:
            raise ValueError("Source name is required")
        return True
    
    def preprocess_text(self, text: str) -> str:
        """
        Предварительная обработка извлеченного текста.
        
        Args:
            text: Исходный текст
            
        Returns:
            Обработанный текст
        """
        # Базовая очистка текста
        text = text.strip()
        # Удаляем множественные переносы строк
        text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
        return text
    
    def get_default_metadata(self, source_input: SourceInput) -> Dict[str, Any]:
        """
        Создает базовые метаданные для источника.
        
        Args:
            source_input: Входные данные источника
            
        Returns:
            Словарь с метаданными
        """
        return {
            "extractor_type": self.__class__.__name__,
            "source_name": source_input.source_name,
            "processed_at": None,  # Будет заполнено при обработке
            **source_input.metadata
        }