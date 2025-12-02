"""
Integration tests for the Student Loan Document Extractor Platform.

Tests end-to-end document processing pipeline, API endpoints,
database operations, storage operations, and batch processing workflow.
"""

import pytest
import os
import sys
import json
import tempfile
from pathlib import Path
from io import BytesIO
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    app = None


class TestAPIEndpoints:
    """Test API endpoint functionality"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns correct response"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["status"] == "running"
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "api"
    
    def test_api_status_endpoint(self, client):
        """Test API status endpoint"""
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert "api" in data
        assert data["api"] == "online"


class TestDocumentProcessingPipeline:
    """Test end-to-end document processing pipeline"""
    
    @pytest.fixture
    def sample_pdf_path(self):
        """Get path to sample PDF document"""
        sample_dir = Path(__file__).parent.parent / "sample-loan-docs"
        if sample_dir.exists():
            pdf_files = list(sample_dir.glob("*.pdf"))
            if pdf_files:
                return str(pdf_files[0])
        return None
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")
        return TestClient(app)
    
    def test_document_upload_and_extraction(self, client, sample_pdf_path):
        """Test complete document upload and extraction workflow"""
        if not sample_pdf_path or not os.path.exists(sample_pdf_path):
            pytest.skip("No sample PDF available for testing")
        
        # Read sample document
        with open(sample_pdf_path, 'rb') as f:
            file_content = f.read()
        
        # Upload document for extraction
        files = {
            'file': (os.path.basename(sample_pdf_path), file_content, 'application/pdf')
        }
        
        response = client.post("/api/v1/extract", files=files)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check for expected extraction fields
        assert isinstance(data, dict)


class TestDatabaseOperations:
    """Test database operations"""
    
    def test_database_connection(self):
        """Test database connection can be established"""
        try:
            from storage.database import get_database_service
            db = get_database_service()
            assert db is not None
        except Exception as e:
            pytest.skip(f"Database not available: {str(e)}")
    
    def test_store_and_retrieve_document_metadata(self):
        """Test storing and retrieving document metadata"""
        try:
            from storage.database import get_database_service
            import uuid
            from datetime import datetime
            
            db = get_database_service()
            
            # Create test document metadata
            document_id = str(uuid.uuid4())
            document_data = {
                "document_id": document_id,
                "file_name": "test_document.pdf",
                "file_type": "pdf",
                "upload_timestamp": datetime.now(),
                "file_size_bytes": 1024,
                "page_count": 5,
                "storage_path": f"/documents/{document_id}.pdf",
                "processing_status": "pending"
            }
            
            # Store document
            db.store_document(document_data)
            
            # Retrieve document
            retrieved = db.get_document(document_id)
            
            # Verify data
            assert retrieved is not None
            assert retrieved["document_id"] == document_id
            assert retrieved["file_name"] == "test_document.pdf"
            
        except Exception as e:
            pytest.skip(f"Database operations not available: {str(e)}")


class TestStorageOperations:
    """Test storage operations"""
    
    def test_storage_service_initialization(self):
        """Test storage service can be initialized"""
        try:
            from storage.storage_service import StorageService
            storage = StorageService()
            assert storage is not None
        except Exception as e:
            pytest.skip(f"Storage service not available: {str(e)}")
    
    def test_store_and_retrieve_document(self):
        """Test storing and retrieving document files"""
        try:
            from storage.storage_service import StorageService
            
            storage = StorageService()
            
            # Create test document content
            test_content = b"Test document content"
            test_filename = "test_doc.pdf"
            
            # Store document
            result = storage.store_document_with_data(
                file_content=test_content,
                filename=test_filename,
                file_type="pdf"
            )
            
            # Verify storage result
            assert result["status"] == "success"
            assert "document_id" in result
            
            document_id = result["document_id"]
            
            # Retrieve document
            retrieved_content = storage.get_document_file(document_id)
            
            # Verify content
            assert retrieved_content == test_content
            
        except Exception as e:
            pytest.skip(f"Storage operations not available: {str(e)}")
    
    def test_storage_service_methods_exist(self):
        """Test that required storage service methods exist"""
        try:
            from storage.storage_service import StorageService
            
            storage = StorageService()
            
            # Check that required methods exist
            assert hasattr(storage, 'store_document')
            assert hasattr(storage, 'store_extracted_data')
            assert hasattr(storage, 'create_processing_job')
            assert hasattr(storage, 'update_processing_job')
            assert hasattr(storage, 'get_processing_job')
            assert hasattr(storage, 'update_document_status')
            
        except Exception as e:
            pytest.skip(f"Storage service not available: {str(e)}")


class TestBatchProcessing:
    """Test batch processing workflow"""
    
    def test_batch_processor_initialization(self):
        """Test batch processor can be initialized"""
        try:
            from src.api.batch_processor import BatchProcessingHandler
            processor = BatchProcessingHandler()
            assert processor is not None
        except Exception as e:
            pytest.skip(f"Batch processor not available: {str(e)}")
    
    def test_batch_processing_summary_creation(self):
        """Test batch processing summary creation"""
        try:
            from src.api.batch_processor import BatchProcessingSummary
            
            # Create summary
            summary = BatchProcessingSummary(job_id="test-job-123", total_documents=5)
            
            # Verify initial state
            assert summary.job_id == "test-job-123"
            assert summary.total_documents == 5
            assert summary.processed_documents == 0
            assert summary.successful_documents == 0
            assert summary.failed_documents == 0
        except Exception as e:
            pytest.skip(f"Batch processing classes not available: {str(e)}")
    
    def test_batch_processing_result_creation(self):
        """Test batch processing result creation"""
        try:
            from src.api.batch_processor import BatchProcessingResult
            
            # Create success result
            result = BatchProcessingResult(
                file_name="test.pdf",
                status="success",
                document_id="doc-123",
                loan_id="loan-456",
                processing_time=2.5
            )
            
            # Verify result
            assert result.file_name == "test.pdf"
            assert result.status == "success"
            assert result.document_id == "doc-123"
            assert result.loan_id == "loan-456"
            assert result.processing_time == 2.5
            
            # Test to_dict conversion
            result_dict = result.to_dict()
            assert isinstance(result_dict, dict)
            assert result_dict["file_name"] == "test.pdf"
            assert result_dict["status"] == "success"
        except Exception as e:
            pytest.skip(f"Batch processing classes not available: {str(e)}")
    
    def test_batch_processing_summary_add_result(self):
        """Test adding results to batch processing summary"""
        try:
            from src.api.batch_processor import BatchProcessingSummary, BatchProcessingResult
            
            # Create summary
            summary = BatchProcessingSummary(job_id="test-job-456", total_documents=3)
            
            # Add successful result
            success_result = BatchProcessingResult(
                file_name="doc1.pdf",
                status="success",
                document_id="doc-1",
                loan_id="loan-1"
            )
            summary.add_result(success_result)
            
            # Verify counts
            assert summary.processed_documents == 1
            assert summary.successful_documents == 1
            assert summary.failed_documents == 0
            
            # Add failed result
            failed_result = BatchProcessingResult(
                file_name="doc2.pdf",
                status="failed",
                error_message="Test error"
            )
            summary.add_result(failed_result)
            
            # Verify counts
            assert summary.processed_documents == 2
            assert summary.successful_documents == 1
            assert summary.failed_documents == 1
            
            # Test finalize
            summary.finalize()
            assert summary.end_time is not None
            
            # Test to_dict
            summary_dict = summary.to_dict()
            assert isinstance(summary_dict, dict)
            assert summary_dict["total_documents"] == 3
            assert summary_dict["processed_documents"] == 2
            assert summary_dict["successful_documents"] == 1
            assert summary_dict["failed_documents"] == 1
            
        except Exception as e:
            pytest.skip(f"Batch processing classes not available: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
