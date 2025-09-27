import re
import requests
from typing import Dict, Any, List
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from .base import DataExtractor, SourceInput, ExtractedData


class WebDataExtractor(DataExtractor):
    """
    Экстрактор для извлечения текста из веб-страниц.
    Поддерживает HTTP и HTTPS ссылки.
    """
    
    def __init__(self, timeout: int = 10, max_content_length: int = 10 * 1024 * 1024):
        """
        Args:
            timeout: Таймаут для HTTP запросов в секундах
            max_content_length: Максимальный размер контента в байтах (по умолчанию 10MB)
        """
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.session = requests.Session()
        # Устанавливаем user-agent для избежания блокировок
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def can_handle(self, source_input: SourceInput) -> bool:
        """Проверяет, является ли источник URL"""
        if not isinstance(source_input.data, str):
            return False
        
        try:
            parsed = urlparse(source_input.data)
            return parsed.scheme in ['http', 'https'] and parsed.netloc
        except Exception:
            return False
    
    def get_supported_types(self) -> List[str]:
        """Возвращает список поддерживаемых типов"""
        return ['web', 'url', 'html']
    
    def extract(self, source_input: SourceInput) -> ExtractedData:
        """Извлекает текст с веб-страницы"""
        self.validate_input(source_input)
        
        if not self.can_handle(source_input):
            raise ValueError(f"Invalid URL: {source_input.data}")
        
        url = source_input.data
        
        try:
            # Выполняем HTTP запрос
            response = self._fetch_url(url)
            
            # Извлекаем текст из HTML
            extracted_text, page_metadata = self._extract_text_from_html(response.text, url)
            
            # Предварительная обработка текста
            processed_text = self.preprocess_text(extracted_text)
            
            # Создаем метаданные
            metadata = self.get_default_metadata(source_input)
            metadata.update({
                "url": url,
                "status_code": response.status_code,
                "content_type": response.headers.get('content-type', ''),
                "content_length": len(response.content),
                "processed_at": datetime.now().isoformat(),
                **page_metadata
            })
            
            return ExtractedData(
                text_content=processed_text,
                metadata=metadata,
                source_type="web"
            )
            
        except Exception as e:
            raise Exception(f"Error extracting text from URL {url}: {str(e)}")
    
    def _fetch_url(self, url: str) -> requests.Response:
        """Выполняет HTTP запрос с проверками безопасности"""
        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                stream=True,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Проверяем размер контента
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_content_length:
                raise ValueError(f"Content too large: {content_length} bytes")
            
            # Проверяем тип контента
            content_type = response.headers.get('content-type', '').lower()
            if not any(ct in content_type for ct in ['text/html', 'application/xhtml', 'text/plain']):
                raise ValueError(f"Unsupported content type: {content_type}")
            
            # Загружаем контент с проверкой размера
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > self.max_content_length:
                    raise ValueError(f"Content too large: exceeds {self.max_content_length} bytes")
            
            response._content = content
            return response
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"HTTP request failed: {str(e)}")
    
    def _extract_text_from_html(self, html_content: str, url: str) -> tuple[str, Dict[str, Any]]:
        """Извлекает текст из HTML контента"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Удаляем ненужные элементы
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript']):
                element.decompose()
            
            # Извлекаем метаданные страницы
            page_metadata = self._extract_page_metadata(soup, url)
            
            # Извлекаем основной текст
            # Ищем основной контент в приоритетном порядке
            main_content = None
            for selector in ['main', 'article', '[role="main"]', '.content', '.post', '.article', '.entry-content']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                # Если не нашли основной контент, берем весь body
                main_content = soup.find('body') or soup
            
            # Извлекаем текст
            text = main_content.get_text(separator='\n', strip=True)
            
            return text, page_metadata
            
        except Exception as e:
            raise Exception(f"Error parsing HTML: {str(e)}")
    
    def _extract_page_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Извлекает метаданные страницы"""
        metadata = {}
        
        # Заголовок страницы
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text(strip=True)
        
        # Meta описание
        description_tag = soup.find('meta', attrs={'name': 'description'})
        if description_tag:
            metadata['description'] = description_tag.get('content', '')
        
        # Meta keywords
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag:
            metadata['keywords'] = keywords_tag.get('content', '')
        
        # Автор
        author_tag = soup.find('meta', attrs={'name': 'author'})
        if author_tag:
            metadata['author'] = author_tag.get('content', '')
        
        # Язык
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            metadata['language'] = html_tag.get('lang')
        
        # Домен
        parsed_url = urlparse(url)
        metadata['domain'] = parsed_url.netloc
        
        return metadata
    
    def validate_input(self, source_input: SourceInput) -> bool:
        """Дополнительная валидация для URL"""
        super().validate_input(source_input)
        
        if not isinstance(source_input.data, str):
            raise ValueError("URL must be a string")
        
        url = source_input.data.strip()
        if not url:
            raise ValueError("URL cannot be empty")
        
        # Проверяем формат URL
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
            
            if parsed.scheme not in ['http', 'https']:
                raise ValueError("Only HTTP and HTTPS URLs are supported")
                
        except Exception:
            raise ValueError("Invalid URL format")
        
        return True
    
    def preprocess_text(self, text: str) -> str:
        """Специализированная обработка текста для веб-страниц"""
        # Базовая обработка
        text = super().preprocess_text(text)
        
        # Удаляем лишние пробелы и переносы
        text = re.sub(r'\s+', ' ', text)
        
        # Восстанавливаем структуру абзацев
        text = re.sub(r'([.!?])\s+', r'\1\n\n', text)
        
        # Удаляем повторяющиеся строки (часто встречается в навигации)
        lines = text.split('\n')
        unique_lines = []
        seen = set()
        for line in lines:
            line = line.strip()
            if line and line not in seen:
                unique_lines.append(line)
                seen.add(line)
        
        return '\n'.join(unique_lines)