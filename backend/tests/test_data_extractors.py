import pytest
import io
from app.services.data_extractors import (
    DataExtractorFactory, 
    SourceInput, 
    FileDataExtractor, 
    WebDataExtractor,
    AudioDataExtractor
)


class TestFileDataExtractor:
    
    def test_can_handle_text_file(self):
        extractor = FileDataExtractor()
        source_input = SourceInput(
            data=io.BytesIO(b"test content"),
            source_name="test.txt",
            metadata={}
        )
        assert extractor.can_handle(source_input) is True
    
    def test_can_handle_pdf_file(self):
        extractor = FileDataExtractor()
        source_input = SourceInput(
            data=io.BytesIO(b"test content"),
            source_name="test.pdf",
            metadata={}
        )
        assert extractor.can_handle(source_input) is True
    
    def test_cannot_handle_unsupported_file(self):
        extractor = FileDataExtractor()
        source_input = SourceInput(
            data=io.BytesIO(b"test content"),
            source_name="test.xyz",
            metadata={}
        )
        assert extractor.can_handle(source_input) is False
    
    def test_cannot_handle_non_file_data(self):
        extractor = FileDataExtractor()
        source_input = SourceInput(
            data="not a file",
            source_name="test.txt",
            metadata={}
        )
        assert extractor.can_handle(source_input) is False
    
    def test_get_supported_types(self):
        extractor = FileDataExtractor()
        types = extractor.get_supported_types()
        assert 'text' in types
        assert 'pdf' in types
        assert 'docx' in types
    
    def test_validate_input_success(self):
        extractor = FileDataExtractor()
        source_input = SourceInput(
            data=io.BytesIO(b"test content"),
            source_name="test.txt",
            metadata={}
        )
        assert extractor.validate_input(source_input) is True
    
    def test_validate_input_empty_file(self):
        extractor = FileDataExtractor()
        source_input = SourceInput(
            data=io.BytesIO(b""),
            source_name="test.txt",
            metadata={}
        )
        with pytest.raises(ValueError, match="File is empty"):
            extractor.validate_input(source_input)
    
    def test_validate_input_wrong_data_type(self):
        extractor = FileDataExtractor()
        source_input = SourceInput(
            data="not bytes",
            source_name="test.txt",
            metadata={}
        )
        with pytest.raises(ValueError, match="File data must be BytesIO or bytes"):
            extractor.validate_input(source_input)


class TestWebDataExtractor:
    
    def test_can_handle_http_url(self):
        extractor = WebDataExtractor()
        source_input = SourceInput(
            data="http://example.com",
            source_name="example.com",
            metadata={}
        )
        assert extractor.can_handle(source_input) is True
    
    def test_can_handle_https_url(self):
        extractor = WebDataExtractor()
        source_input = SourceInput(
            data="https://example.com",
            source_name="example.com",
            metadata={}
        )
        assert extractor.can_handle(source_input) is True
    
    def test_cannot_handle_non_url(self):
        extractor = WebDataExtractor()
        source_input = SourceInput(
            data="not a url",
            source_name="test",
            metadata={}
        )
        assert extractor.can_handle(source_input) is False
    
    def test_cannot_handle_invalid_url(self):
        extractor = WebDataExtractor()
        source_input = SourceInput(
            data="ftp://example.com",
            source_name="test",
            metadata={}
        )
        assert extractor.can_handle(source_input) is False
    
    def test_get_supported_types(self):
        extractor = WebDataExtractor()
        types = extractor.get_supported_types()
        assert 'web' in types
        assert 'url' in types
        assert 'html' in types
    
    def test_validate_input_success(self):
        extractor = WebDataExtractor()
        source_input = SourceInput(
            data="https://example.com",
            source_name="example.com",
            metadata={}
        )
        assert extractor.validate_input(source_input) is True
    
    def test_validate_input_empty_url(self):
        extractor = WebDataExtractor()
        source_input = SourceInput(
            data="",
            source_name="test",
            metadata={}
        )
        with pytest.raises(ValueError, match="URL cannot be empty"):
            extractor.validate_input(source_input)
    
    def test_validate_input_invalid_scheme(self):
        extractor = WebDataExtractor()
        source_input = SourceInput(
            data="ftp://example.com",
            source_name="test",
            metadata={}
        )
        with pytest.raises(ValueError, match="Only HTTP and HTTPS URLs are supported"):
            extractor.validate_input(source_input)


class TestAudioDataExtractor:
    
    def test_can_handle_mp3_file(self):
        # Skip if audio extractor not available
        try:
            extractor = AudioDataExtractor(groq_api_key="test_key")
        except ImportError:
            pytest.skip("Audio dependencies not available")
        
        source_input = SourceInput(
            data=io.BytesIO(b"fake audio content"),
            source_name="test.mp3",
            metadata={}
        )
        assert extractor.can_handle(source_input) is True
    
    def test_can_handle_wav_file(self):
        try:
            extractor = AudioDataExtractor(groq_api_key="test_key")
        except ImportError:
            pytest.skip("Audio dependencies not available")
        
        source_input = SourceInput(
            data=io.BytesIO(b"fake audio content"),
            source_name="test.wav",
            metadata={}
        )
        assert extractor.can_handle(source_input) is True
    
    def test_cannot_handle_unsupported_audio(self):
        try:
            extractor = AudioDataExtractor(groq_api_key="test_key")
        except ImportError:
            pytest.skip("Audio dependencies not available")
        
        source_input = SourceInput(
            data=io.BytesIO(b"fake content"),
            source_name="test.xyz",
            metadata={}
        )
        assert extractor.can_handle(source_input) is False
    
    def test_get_supported_types(self):
        try:
            extractor = AudioDataExtractor(groq_api_key="test_key")
        except ImportError:
            pytest.skip("Audio dependencies not available")
        
        types = extractor.get_supported_types()
        assert 'audio' in types
        assert 'speech' in types
        assert 'transcription' in types


class TestDataExtractorFactory:
    
    def test_factory_initialization(self):
        factory = DataExtractorFactory()
        assert len(factory._extractors) >= 2  # At least file and web extractors
    
    def test_get_extractor_for_text_file(self):
        factory = DataExtractorFactory()
        source_input = SourceInput(
            data=io.BytesIO(b"test content"),
            source_name="test.txt",
            metadata={}
        )
        extractor = factory.get_extractor(source_input)
        assert isinstance(extractor, FileDataExtractor)
    
    def test_get_extractor_for_url(self):
        factory = DataExtractorFactory()
        source_input = SourceInput(
            data="https://example.com",
            source_name="example.com",
            metadata={}
        )
        extractor = factory.get_extractor(source_input)
        assert isinstance(extractor, WebDataExtractor)
    
    def test_get_extractor_for_unsupported_source(self):
        factory = DataExtractorFactory()
        source_input = SourceInput(
            data=12345,  # Unsupported data type
            source_name="test",
            metadata={}
        )
        with pytest.raises(ValueError, match="No suitable extractor found"):
            factory.get_extractor(source_input)
    
    def test_detect_source_type_url(self):
        source_type = DataExtractorFactory.detect_source_type("https://example.com", "example.com")
        assert source_type == "web"
    
    def test_detect_source_type_text_file(self):
        source_type = DataExtractorFactory.detect_source_type(b"content", "test.txt")
        assert source_type == "file"
    
    def test_detect_source_type_audio_file(self):
        source_type = DataExtractorFactory.detect_source_type(b"content", "test.mp3")
        assert source_type == "audio"
    
    def test_detect_source_type_unknown(self):
        source_type = DataExtractorFactory.detect_source_type(12345, "test")
        assert source_type == "unknown"
    
    def test_create_source_input(self):
        source_input = DataExtractorFactory.create_source_input(
            data="https://example.com",
            source_name="example.com",
            metadata={"custom": "data"}
        )
        assert source_input.data == "https://example.com"
        assert source_input.source_name == "example.com"
        assert source_input.metadata["custom"] == "data"
        assert source_input.metadata["detected_type"] == "web"
    
    def test_get_all_supported_types(self):
        factory = DataExtractorFactory()
        supported_types = factory.get_all_supported_types()
        assert isinstance(supported_types, dict)
        assert "FileDataExtractor" in supported_types
        assert "WebDataExtractor" in supported_types
    
    def test_list_available_extractors(self):
        factory = DataExtractorFactory()
        extractors_info = factory.list_available_extractors()
        assert isinstance(extractors_info, list)
        assert len(extractors_info) >= 2
        
        # Check structure of extractor info
        extractor_info = extractors_info[0]
        assert "name" in extractor_info
        assert "supported_types" in extractor_info
        assert "description" in extractor_info


if __name__ == "__main__":
    pytest.main([__file__])