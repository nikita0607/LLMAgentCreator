import io
import os
import tempfile
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

from .base import DataExtractor, SourceInput, ExtractedData


class AudioDataExtractor(DataExtractor):
    """
    Экстрактор для транскрибации аудио файлов в текст.
    Поддерживает различные аудио форматы: MP3, WAV, M4A, FLAC, OGG
    
    Может использовать:
    1. OpenAI Whisper (локально)
    2. Groq API для транскрибации
    """
    
    SUPPORTED_EXTENSIONS = {
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav', 
        '.m4a': 'audio/mp4',
        '.flac': 'audio/flac',
        '.ogg': 'audio/ogg',
        '.opus': 'audio/opus'
    }
    
    def __init__(self, groq_api_key: Optional[str] = None, whisper_model: str = "base"):
        """
        Args:
            groq_api_key: API ключ для Groq (если используется)
            whisper_model: Модель Whisper для локальной транскрибации
        """
        self.groq_api_key = groq_api_key
        self.whisper_model = whisper_model
        self._whisper = None
        self._groq_client = None
        
        # Определяем доступные методы транскрибации
        self.transcription_methods = []
        
        if groq_api_key and GROQ_AVAILABLE:
            self._groq_client = Groq(api_key=groq_api_key)
            self.transcription_methods.append("groq")
        
        if WHISPER_AVAILABLE:
            self.transcription_methods.append("whisper")
        
        if not self.transcription_methods:
            raise ImportError("No transcription methods available. Install 'openai-whisper' or provide Groq API key")
    
    def can_handle(self, source_input: SourceInput) -> bool:
        """Проверяет, может ли обработать аудио файл"""
        if not isinstance(source_input.data, (io.BytesIO, bytes)):
            return False
        
        # Проверяем расширение файла
        _, ext = os.path.splitext(source_input.source_name.lower())
        return ext in self.SUPPORTED_EXTENSIONS
    
    def get_supported_types(self) -> List[str]:
        """Возвращает список поддерживаемых типов аудио"""
        return ['audio', 'speech', 'transcription']
    
    def extract(self, source_input: SourceInput) -> ExtractedData:
        """Транскрибирует аудио файл в текст"""
        self.validate_input(source_input)
        
        if not self.can_handle(source_input):
            raise ValueError(f"Unsupported audio file type for {source_input.source_name}")
        
        _, ext = os.path.splitext(source_input.source_name.lower())
        
        try:
            # Выполняем транскрибацию
            transcription_result = self._transcribe_audio(source_input.data, source_input.source_name)
            
            # Предварительная обработка текста
            processed_text = self.preprocess_text(transcription_result['text'])
            
            # Создаем метаданные
            metadata = self.get_default_metadata(source_input)
            metadata.update({
                "audio_format": ext,
                "mime_type": self.SUPPORTED_EXTENSIONS[ext],
                "file_size": len(source_input.data.getvalue()) if hasattr(source_input.data, 'getvalue') else None,
                "transcription_method": transcription_result['method'],
                "language": transcription_result.get('language'),
                "confidence": transcription_result.get('confidence'),
                "duration": transcription_result.get('duration'),
                "processed_at": datetime.now().isoformat()
            })
            
            return ExtractedData(
                text_content=processed_text,
                metadata=metadata,
                source_type="audio"
            )
            
        except Exception as e:
            raise Exception(f"Error transcribing audio file {source_input.source_name}: {str(e)}")
    
    def _transcribe_audio(self, audio_data: io.BytesIO, filename: str) -> Dict[str, Any]:
        """Выполняет транскрибацию аудио"""
        # Пробуем методы в порядке приоритета
        for method in self.transcription_methods:
            try:
                if method == "groq":
                    return self._transcribe_with_groq(audio_data, filename)
                elif method == "whisper":
                    return self._transcribe_with_whisper(audio_data, filename)
            except Exception as e:
                print(f"Transcription with {method} failed: {e}")
                continue
        
        raise Exception("All transcription methods failed")
    
    def _transcribe_with_groq(self, audio_data: io.BytesIO, filename: str) -> Dict[str, Any]:
        """Транскрибация через Groq API"""
        if not self._groq_client:
            raise Exception("Groq client not initialized")
        
        # Сохраняем во временный файл для Groq API
        _, ext = os.path.splitext(filename.lower())
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
            if isinstance(audio_data, io.BytesIO):
                tmp_file.write(audio_data.getvalue())
            else:
                tmp_file.write(audio_data)
            tmp_path = tmp_file.name
        
        try:
            with open(tmp_path, "rb") as audio_file:
                transcription = self._groq_client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3",
                    response_format="verbose_json"
                )
            
            return {
                "text": transcription.text,
                "method": "groq",
                "language": getattr(transcription, 'language', None),
                "duration": getattr(transcription, 'duration', None)
            }
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def _transcribe_with_whisper(self, audio_data: io.BytesIO, filename: str) -> Dict[str, Any]:
        """Транскрибация через локальный Whisper"""
        if not WHISPER_AVAILABLE:
            raise Exception("Whisper not available")
        
        # Загружаем модель если еще не загружена
        if self._whisper is None:
            self._whisper = whisper.load_model(self.whisper_model)
        
        # Сохраняем во временный файл
        _, ext = os.path.splitext(filename.lower())
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
            if isinstance(audio_data, io.BytesIO):
                tmp_file.write(audio_data.getvalue())
            else:
                tmp_file.write(audio_data)
            tmp_path = tmp_file.name
        
        try:
            result = self._whisper.transcribe(tmp_path, verbose=False)
            
            return {
                "text": result["text"],
                "method": "whisper",
                "language": result.get("language"),
                "duration": result.get("duration")
            }
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def validate_input(self, source_input: SourceInput) -> bool:
        """Дополнительная валидация для аудио файлов"""
        super().validate_input(source_input)
        
        if not isinstance(source_input.data, (io.BytesIO, bytes)):
            raise ValueError("Audio data must be BytesIO or bytes")
        
        if not source_input.source_name:
            raise ValueError("Audio filename is required")
        
        # Проверяем размер файла
        max_size = 25 * 1024 * 1024  # 25MB лимит для большинства API
        if isinstance(source_input.data, io.BytesIO):
            size = len(source_input.data.getvalue())
        else:
            size = len(source_input.data)
        
        if size > max_size:
            raise ValueError(f"Audio file too large: {size} bytes (max {max_size})")
        
        if size == 0:
            raise ValueError("Audio file is empty")
        
        return True
    
    def preprocess_text(self, text: str) -> str:
        """Специализированная обработка текста для транскрибации"""
        # Базовая обработка
        text = super().preprocess_text(text)
        
        # Удаляем повторяющиеся фразы (часто встречается в транскрибации)
        words = text.split()
        cleaned_words = []
        prev_word = ""
        
        for word in words:
            if word.lower() != prev_word.lower():
                cleaned_words.append(word)
            prev_word = word
        
        text = " ".join(cleaned_words)
        
        # Добавляем пунктуацию на основе пауз
        # Это упрощенная версия, можно улучшить
        import re
        text = re.sub(r'\s+', ' ', text)  # Нормализуем пробелы
        
        return text