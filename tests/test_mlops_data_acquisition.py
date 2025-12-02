"""Unit tests for data acquisition module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mlops.data_acquisition import (
    DataAcquisition,
    DataAcquisitionConfig,
    DocumentMetadata,
    DataAcquisitionError
)


class TestDataAcquisitionConfig:
    """Test DataAcquisitionConfig model."""
    
    def test_config_creation_with_defaults(self):
        """Test configuration creation with default values."""
        config = DataAcquisitionConfig(
            s3_endpoint="http://localhost:9000",
            s3_access_key="test",
            s3_secret_key="test",
            s3_bucket_name="test-bucket",
            database_url="postgresql://test",
            api_base_url="http://localhost:8000",
            api_key="test-key"
        )
        
        assert config.max_retries == 3
        assert config.timeout_seconds == 30
        assert config.output_dir == Path("data/raw")
    
    def test_config_validation_max_retries(self):
        """Test validation of max_retries field."""
        with pytest.raises(ValueError):
            DataAcquisitionConfig(
                s3_endpoint="http://localhost:9000",
                s3_access_key="test",
                s3_secret_key="test",
                s3_bucket_name="test",
                database_url="postgresql://test",
                api_base_url="http://localhost:8000",
                api_key="test",
                max_retries=0  # Invalid: must be >= 1
            )


class TestDocumentMetadata:
    """Test DocumentMetadata model."""
    
    def test_metadata_creation_valid(self):
        """Test creating valid document metadata."""
        from datetime import datetime
        
        metadata = DocumentMetadata(
            document_id="doc-001",
            file_name="test.pdf",
            file_type="pdf",
            file_size_bytes=1024,
            page_count=5,
            storage_path="documents/test.pdf",
            upload_timestamp=datetime.utcnow(),
            processing_status="pending"
        )
        
        assert metadata.document_id == "doc-001"
        assert metadata.file_type == "pdf"
    
    def test_metadata_invalid_file_type(self):
        """Test metadata validation with invalid file type."""
        from datetime import datetime
        
        with pytest.raises(ValueError):
            DocumentMetadata(
                document_id="doc-001",
                file_name="test.doc",
                file_type="doc",  # Invalid type
                file_size_bytes=1024,
                storage_path="documents/test.doc",
                upload_timestamp=datetime.utcnow()
            )


class TestDataAcquisition:
    """Test DataAcquisition class."""
    
    @pytest.fixture
    def config(self, tmp_path):
        """Create test configuration."""
        return DataAcquisitionConfig(
            s3_endpoint="http://localhost:9000",
            s3_access_key="test",
            s3_secret_key="test",
            s3_bucket_name="test-bucket",
            database_url="postgresql://test:test@localhost/test",
            api_base_url="http://localhost:8000",
            api_key="test-key",
            output_dir=tmp_path / "raw"
        )
    
    @patch('mlops.data_acquisition.boto3.client')
    def test_initialization(self, mock_boto_client, config):
        """Test DataAcquisition initialization."""
        acquisition = DataAcquisition(config)
        
        assert acquisition.config == config
        assert acquisition.output_dir.exists()
        mock_boto_client.assert_called_once()
    
    @patch('mlops.data_acquisition.psycopg2.connect')
    @patch('mlops.data_acquisition.boto3.client')
    def test_fetch_pending_documents_success(self, mock_boto, mock_connect, config):
        """Test fetching pending documents from database."""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "document_id": "doc-001",
                "file_name": "test.pdf",
                "file_type": "pdf",
                "file_size_bytes": 1024,
                "page_count": 5,
                "storage_path": "documents/test.pdf",
                "upload_timestamp": "2025-01-01T00:00:00",
                "processing_status": "pending"
            }
        ]
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        acquisition = DataAcquisition(config)
        documents = acquisition.fetch_pending_documents()
        
        assert len(documents) == 1
        assert documents[0].document_id == "doc-001"
        mock_connect.assert_called_once()
    
    @patch('mlops.data_acquisition.psycopg2.connect')
    @patch('mlops.data_acquisition.boto3.client')
    def test_fetch_pending_documents_database_error(self, mock_boto, mock_connect, config):
        """Test handling of database errors."""
        mock_connect.side_effect = Exception("Database connection failed")
        
        acquisition = DataAcquisition(config)
        
        with pytest.raises(DataAcquisitionError):
            acquisition.fetch_pending_documents()
    
    @patch('mlops.data_acquisition.boto3.client')
    def test_validate_document_format_valid(self, mock_boto, config, tmp_path):
        """Test document format validation with valid file."""
        # Create test file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"test content")
        
        acquisition = DataAcquisition(config)
        result = acquisition.validate_document_format(test_file)
        
        assert result is True
    
    @patch('mlops.data_acquisition.boto3.client')
    def test_validate_document_format_invalid_extension(self, mock_boto, config, tmp_path):
        """Test document format validation with invalid extension."""
        test_file = tmp_path / "test.doc"
        test_file.write_bytes(b"test content")
        
        acquisition = DataAcquisition(config)
        result = acquisition.validate_document_format(test_file)
        
        assert result is False
    
    @patch('mlops.data_acquisition.boto3.client')
    def test_validate_document_format_too_large(self, mock_boto, config, tmp_path):
        """Test document format validation with file too large."""
        test_file = tmp_path / "large.pdf"
        # Create file larger than 50MB
        test_file.write_bytes(b"x" * (51 * 1024 * 1024))
        
        acquisition = DataAcquisition(config)
        result = acquisition.validate_document_format(test_file)
        
        assert result is False
    
    @patch('mlops.data_acquisition.boto3.client')
    def test_validate_document_format_nonexistent_file(self, mock_boto, config):
        """Test document format validation with nonexistent file."""
        acquisition = DataAcquisition(config)
        result = acquisition.validate_document_format(Path("nonexistent.pdf"))
        
        assert result is False


@pytest.mark.integration
class TestDataAcquisitionIntegration:
    """Integration tests for DataAcquisition."""
    
    @pytest.fixture
    def config(self, tmp_path):
        """Create test configuration."""
        return DataAcquisitionConfig(
            s3_endpoint="http://localhost:9000",
            s3_access_key="minioadmin",
            s3_secret_key="minioadmin123",
            s3_bucket_name="test-bucket",
            database_url="postgresql://loanuser:loanpass123@localhost/loanextractor",
            api_base_url="http://localhost:8000",
            api_key="",
            output_dir=tmp_path / "raw"
        )
    
    @pytest.mark.skip(reason="Requires running services")
    def test_full_acquisition_pipeline(self, config):
        """Test complete acquisition pipeline (requires services)."""
        acquisition = DataAcquisition(config)
        stats = acquisition.run()
        
        assert "total_documents" in stats
        assert "downloaded" in stats
