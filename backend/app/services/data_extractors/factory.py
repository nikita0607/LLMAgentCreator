from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
import os

from .base import DataExtractor, SourceInput
from .file_extractor import FileDataExtractor
from .web_extractor import WebDataExtractor
from .audio_extractor import AudioDataExtractor


class DataExtractorFactory:
    """
    Фабрика для автоматического выбора подходящего экстрактора данных.
    
    Определяет тип источника и возвращает соответствующий экстрактор.
    """
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """
        Args:
            groq_api_key: API ключ для Groq (для аудио транскрибации)
        """
        self.groq_api_key = groq_api_key
        self._extractors: List[DataExtractor] = []
        self._initialize_extractors()
    
    def _initialize_extractors(self):
        """Инициализирует все доступные экстракторы"""
        # Порядок важен - первый подходящий экстрактор будет использован
        
        # Аудио экстрактор (должен быть перед файловым, т.к. также работает с файлами)
        try:
            audio_extractor = AudioDataExtractor(groq_api_key=self.groq_api_key)
            self._extractors.append(audio_extractor)
        except ImportError:
            print("Warning: AudioDataExtractor not available (missing dependencies)")
        
        # Веб экстрактор
        self._extractors.append(WebDataExtractor())
        
        # Файловый экстрактор (последний, т.к. наиболее общий)
        self._extractors.append(FileDataExtractor())
    
    def get_extractor(self, source_input: SourceInput) -> DataExtractor:
        """
        Возвращает подходящий экстрактор для данного источника.
        
        Args:
            source_input: Входные данные источника
            
        Returns:
            Подходящий экстрактор
            
        Raises:
            ValueError: Если не найден подходящий экстрактор
        """
        for extractor in self._extractors:
            if extractor.can_handle(source_input):
                return extractor
        
        raise ValueError(f"No suitable extractor found for source: {source_input.source_name}")
    
    def get_extractors_by_type(self, source_type: str) -> List[DataExtractor]:
        """
        Возвращает все экстракторы, поддерживающие указанный тип.
        
        Args:
            source_type: Тип источника
            
        Returns:
            Список подходящих экстракторов
        """
        matching_extractors = []
        for extractor in self._extractors:
            if source_type in extractor.get_supported_types():
                matching_extractors.append(extractor)
        return matching_extractors
    
    def get_all_supported_types(self) -> Dict[str, List[str]]:
        """
        Возвращает все поддерживаемые типы источников.
        
        Returns:
            Словарь {имя_экстрактора: [список_типов]}
        """
        supported_types = {}
        for extractor in self._extractors:
            extractor_name = extractor.__class__.__name__
            supported_types[extractor_name] = extractor.get_supported_types()
        return supported_types
    
    @staticmethod
    def detect_source_type(data: Any, source_name: str) -> str:
        """
        Автоматически определяет тип источника данных.
        
        Args:
            data: Данные источника
            source_name: Имя источника
            
        Returns:
            Строка с типом источника
        """
        # Если это строка, проверяем, является ли она URL
        if isinstance(data, str):
            try:
                parsed = urlparse(data.strip())
                if parsed.scheme in ['http', 'https'] and parsed.netloc:
                    return "web"
            except Exception:
                pass
            return "text"
        
        # Если это файловые данные, определяем по расширению
        if hasattr(data, 'read') or isinstance(data, (bytes, type(b''))):
            if source_name:
                _, ext = os.path.splitext(source_name.lower())
                
                # Аудио форматы
                audio_exts = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.opus'}
                if ext in audio_exts:
                    return "audio"
                
                # Документы
                doc_exts = {'.txt', '.pdf', '.docx', '.doc'}
                if ext in doc_exts:
                    return "file"
                
                # Изображения (для будущего расширения)
                image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
                if ext in image_exts:
                    return "image"
        
        return "unknown"
    
    @staticmethod
    def create_source_input(data: Any, source_name: str, metadata: Optional[Dict[str, Any]] = None) -> SourceInput:
        """
        Создает SourceInput с автоматически определенным типом.
        
        Args:
            data: Данные источника
            source_name: Имя источника
            metadata: Дополнительные метаданные
            
        Returns:
            SourceInput объект
        """
        if metadata is None:
            metadata = {}
        
        # Добавляем автоматически определенный тип
        detected_type = DataExtractorFactory.detect_source_type(data, source_name)
        metadata['detected_type'] = detected_type
        
        return SourceInput(
            data=data,
            source_name=source_name,
            metadata=metadata
        )
    
    def extract_from_source(self, data: Any, source_name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Удобный метод для извлечения данных из источника в один вызов.
        
        Args:
            data: Данные источника
            source_name: Имя источника
            metadata: Дополнительные метаданные
            
        Returns:
            ExtractedData объект с извлеченными данными
        """
        source_input = self.create_source_input(data, source_name, metadata)
        extractor = self.get_extractor(source_input)
        return extractor.extract(source_input)
    
    def list_available_extractors(self) -> List[Dict[str, Any]]:
        """
        Возвращает информацию о всех доступных экстракторах.
        
        Returns:
            Список словарей с информацией об экстракторах
        """
        extractors_info = []
        for extractor in self._extractors:
            info = {
                "name": extractor.__class__.__name__,
                "supported_types": extractor.get_supported_types(),
                "description": extractor.__class__.__doc__ or "No description available"
            }
            extractors_info.append(info)
        return extractors_info