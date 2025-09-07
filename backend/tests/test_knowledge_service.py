import pytest
import io
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models.knowledge_base import KnowledgeNode, KnowledgeEmbedding
from app.services.knowledge_service import KnowledgeService


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create the tables
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def knowledge_service(db_session):
    """Create a KnowledgeService instance with mocked dependencies"""
    with patch('app.services.knowledge_service.HuggingFaceEmbeddings') as mock_embeddings:
        # Mock the embeddings model
        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_documents.return_value = [
            [0.1, 0.2, 0.3] * 128  # 384-dimensional vector
        ]
        mock_embeddings_instance.embed_query.return_value = [0.1, 0.2, 0.3] * 128
        mock_embeddings.return_value = mock_embeddings_instance
        
        service = KnowledgeService(db_session)
        yield service


class TestKnowledgeService:
    
    def test_init(self, db_session):
        """Test KnowledgeService initialization"""
        with patch('app.services.knowledge_service.HuggingFaceEmbeddings'):
            service = KnowledgeService(db_session)
            assert service.db == db_session
            assert service.extractor_factory is not None
    
    def test_add_document_compatibility(self, knowledge_service, db_session):
        """Test backward compatibility of add_document method"""
        test_content = b"This is a test document content."
        test_file = io.BytesIO(test_content)
        
        with patch.object(knowledge_service.extractor_factory, 'extract_from_source') as mock_extract:
            mock_extract.return_value = Mock(
                text_content="This is a test document content.",
                metadata={"file_type": "text", "extractor_type": "FileDataExtractor"},
                source_type="file"
            )
            
            kb_node = knowledge_service.add_document(
                agent_id=1,
                node_id="test_node",
                file=test_file,
                filename="test.txt"
            )
            
            assert kb_node.agent_id == 1
            assert kb_node.node_id == "test_node"
            assert kb_node.name == "test.txt"
            assert kb_node.source_type == "file"
    
    def test_add_url_source(self, knowledge_service, db_session):
        """Test adding URL as knowledge source"""
        test_url = "https://example.com"
        
        with patch.object(knowledge_service.extractor_factory, 'extract_from_source') as mock_extract:
            mock_extract.return_value = Mock(
                text_content="This is extracted web content.",
                metadata={"url": test_url, "extractor_type": "WebDataExtractor"},
                source_type="web"
            )
            
            kb_node = knowledge_service.add_url(
                agent_id=1,
                node_id="test_url_node",
                url=test_url
            )
            
            assert kb_node.agent_id == 1
            assert kb_node.node_id == "test_url_node"
            assert kb_node.name == test_url
            assert kb_node.source_type == "web"
    
    def test_add_audio_source(self, knowledge_service, db_session):
        """Test adding audio file as knowledge source"""
        test_audio = io.BytesIO(b"fake audio content")
        
        with patch.object(knowledge_service.extractor_factory, 'extract_from_source') as mock_extract:
            mock_extract.return_value = Mock(
                text_content="This is transcribed audio content.",
                metadata={"filename": "test.mp3", "extractor_type": "AudioDataExtractor"},
                source_type="audio"
            )
            
            kb_node = knowledge_service.add_audio(
                agent_id=1,
                node_id="test_audio_node",
                audio_file=test_audio,
                filename="test.mp3"
            )
            
            assert kb_node.agent_id == 1
            assert kb_node.node_id == "test_audio_node"
            assert kb_node.name == "test.mp3"
            assert kb_node.source_type == "audio"
    
    def test_create_or_update_knowledge_node_new(self, knowledge_service, db_session):
        """Test creating a new knowledge node"""
        kb_node = knowledge_service._create_or_update_knowledge_node(
            agent_id=1,
            node_id="new_node",
            source_name="test_source",
            source_type="file",
            source_data={"test": "data"},
            extractor_metadata={"extractor": "metadata"}
        )
        
        assert kb_node.agent_id == 1
        assert kb_node.node_id == "new_node"
        assert kb_node.name == "test_source"
        assert kb_node.source_type == "file"
        assert kb_node.source_data == {"test": "data"}
        assert kb_node.extractor_metadata == {"extractor": "metadata"}
        
        # Verify it's in the database
        db_node = db_session.query(KnowledgeNode).filter_by(id=kb_node.id).first()
        assert db_node is not None
        assert db_node.node_id == "new_node"
    
    def test_create_or_update_knowledge_node_update(self, knowledge_service, db_session):
        """Test updating an existing knowledge node"""
        # Create initial node
        initial_node = KnowledgeNode(
            agent_id=1,
            node_id="existing_node",
            name="old_name",
            source_type="old_type",
            source_data={"old": "data"},
            extractor_metadata={"old": "metadata"}
        )
        db_session.add(initial_node)
        db_session.commit()
        db_session.refresh(initial_node)
        
        # Update the node
        updated_node = knowledge_service._create_or_update_knowledge_node(
            agent_id=1,
            node_id="existing_node",
            source_name="new_name",
            source_type="new_type",
            source_data={"new": "data"},
            extractor_metadata={"new": "metadata"}
        )
        
        assert updated_node.id == initial_node.id  # Same node
        assert updated_node.name == "new_name"
        assert updated_node.source_type == "new_type"
        assert updated_node.source_data == {"new": "data"}
        assert updated_node.extractor_metadata == {"new": "metadata"}
    
    def test_create_embeddings_for_node(self, knowledge_service, db_session):
        """Test creating embeddings for a knowledge node"""
        # Create a knowledge node
        kb_node = KnowledgeNode(
            agent_id=1,
            node_id="test_node",
            name="test",
            source_type="file"
        )
        db_session.add(kb_node)
        db_session.commit()
        db_session.refresh(kb_node)
        
        # Create embeddings
        test_text = "This is a test document with multiple sentences. It should be split into chunks."
        
        knowledge_service._create_embeddings_for_node(kb_node, test_text)
        
        # Verify embeddings were created
        embeddings = db_session.query(KnowledgeEmbedding).filter_by(kb_id=kb_node.id).all()
        assert len(embeddings) > 0
        
        for embedding in embeddings:
            assert embedding.kb_id == kb_node.id
            assert embedding.text_chunk is not None
            assert embedding.embedding is not None
    
    def test_search_embeddings(self, knowledge_service, db_session):
        """Test searching embeddings"""
        # Create a knowledge node with embeddings
        kb_node = KnowledgeNode(
            agent_id=1,
            node_id="search_test_node",
            name="test",
            source_type="file"
        )
        db_session.add(kb_node)
        db_session.commit()
        db_session.refresh(kb_node)
        
        # Add some test embeddings
        embedding1 = KnowledgeEmbedding(
            kb_id=kb_node.id,
            chunk_index=0,
            embedding=[0.1, 0.2, 0.3] * 128,  # 384-dimensional
            text_chunk="This is the first test chunk."
        )
        embedding2 = KnowledgeEmbedding(
            kb_id=kb_node.id,
            chunk_index=1,
            embedding=[0.2, 0.3, 0.4] * 128,  # 384-dimensional
            text_chunk="This is the second test chunk."
        )
        
        db_session.add_all([embedding1, embedding2])
        db_session.commit()
        
        # Search embeddings
        results = knowledge_service.search_embeddings(
            agent_id=1,
            node_id="search_test_node",
            query="test query",
            top_k=2
        )
        
        assert len(results) == 2
        for result in results:
            emb_id, text_chunk, score = result
            assert isinstance(emb_id, int)
            assert isinstance(text_chunk, str)
            assert isinstance(score, float)
    
    def test_get_source_info(self, knowledge_service, db_session):
        """Test getting source information"""
        # Create a knowledge node
        kb_node = KnowledgeNode(
            agent_id=1,
            node_id="info_test_node",
            name="test_source",
            source_type="file",
            source_data={"test": "data"},
            extractor_metadata={"extractor": "metadata"}
        )
        db_session.add(kb_node)
        db_session.commit()
        db_session.refresh(kb_node)
        
        # Get source info
        info = knowledge_service.get_source_info(agent_id=1, node_id="info_test_node")
        
        assert info is not None
        assert info["id"] == kb_node.id
        assert info["agent_id"] == 1
        assert info["node_id"] == "info_test_node"
        assert info["name"] == "test_source"
        assert info["source_type"] == "file"
        assert info["source_data"] == {"test": "data"}
        assert info["extractor_metadata"] == {"extractor": "metadata"}
        assert info["embeddings_count"] == 0
    
    def test_get_source_info_not_found(self, knowledge_service, db_session):
        """Test getting info for non-existent source"""
        info = knowledge_service.get_source_info(agent_id=999, node_id="nonexistent")
        assert info is None
    
    def test_get_supported_source_types(self, knowledge_service):
        """Test getting supported source types"""
        supported_types = knowledge_service.get_supported_source_types()
        
        assert isinstance(supported_types, dict)
        assert len(supported_types) > 0
        
        # Should contain at least file and web extractors
        extractor_names = list(supported_types.keys())
        assert any("FileDataExtractor" in name for name in extractor_names)
        assert any("WebDataExtractor" in name for name in extractor_names)


if __name__ == "__main__":
    pytest.main([__file__])