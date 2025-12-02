"""Data acquisition module for fetching documents from multiple sources.

This module handles document retrieval from:
- MinIO object storage
- REST API endpoints
- PostgreSQL metadata database
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DocumentMetadata(BaseModel):
    """Document metadata model."""
    
    document_id: str
    file_name: str
    file_type: str = Field(..., pattern="^(pdf|jpeg|png|tiff)$")
    file_size_bytes: int = Field(..., gt=0)
    page_count: Optional[int] = Field(None, ge=1, le=50)
    storage_path: str
    upload_timestamp: datetime
    processing_status: str = Field("pending", pattern="^(pending|processing|completed|failed)$")


class DataAcquisitionConfig(BaseModel):
    """Configuration for data acquisition."""
    
    # MinIO/S3 Configuration
    s3_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket_name: str
    
    # Database Configuration
    database_url: str
    
    # API Configuration
    api_base_url: str
    api_key: str
    
    # Processing Configuration
    output_dir: Path = Field(default=Path("data/raw"))
    max_retries: int = Field(default=3, ge=1, le=10)
    timeout_seconds: int = Field(default=30, ge=5, le=300)


class DataAcquisitionError(Exception):
    """Custom exception for data acquisition failures."""
    pass


class DataAcquisition:
    """Main class for acquiring documents from multiple sources."""
    
    def __init__(self, config: DataAcquisitionConfig):
        """Initialize data acquisition with configuration.
        
        Args:
            config: DataAcquisitionConfig instance with source connections
        """
        self.config = config
        self.output_dir = config.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=config.s3_endpoint,
            aws_access_key_id=config.s3_access_key,
            aws_secret_access_key=config.s3_secret_key
        )
        
        logger.info("DataAcquisition initialized successfully")
    
    def fetch_pending_documents(self) -> List[DocumentMetadata]:
        """Fetch list of pending documents from database.
        
        Returns:
            List of DocumentMetadata for pending documents
            
        Raises:
            DataAcquisitionError: If database query fails
        """
        try:
            conn = psycopg2.connect(self.config.database_url)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT document_id, file_name, file_type, file_size_bytes,
                       page_count, storage_path, upload_timestamp, processing_status
                FROM documents
                WHERE processing_status = 'pending'
                ORDER BY upload_timestamp ASC
                LIMIT 100
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            documents = [DocumentMetadata(**row) for row in rows]
            logger.info(f"Fetched {len(documents)} pending documents from database")
            
            return documents
            
        except psycopg2.Error as e:
            logger.error(f"Database error fetching documents: {e}")
            raise DataAcquisitionError(f"Database query failed: {e}") from e
        except Exception as e:
            logger.exception("Unexpected error fetching documents")
            raise DataAcquisitionError(f"Unexpected error: {e}") from e
    
    def download_from_storage(
        self,
        document: DocumentMetadata
    ) -> Path:
        """Download document from MinIO/S3 storage.
        
        Args:
            document: DocumentMetadata with storage path
            
        Returns:
            Path to downloaded file
            
        Raises:
            DataAcquisitionError: If download fails
        """
        try:
            output_path = self.output_dir / document.file_name
            
            # Download from S3
            self.s3_client.download_file(
                self.config.s3_bucket_name,
                document.storage_path,
                str(output_path)
            )
            
            logger.info(f"Downloaded {document.file_name} from storage")
            return output_path
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"S3 download error ({error_code}): {e}")
            raise DataAcquisitionError(f"S3 download failed: {error_code}") from e
        except Exception as e:
            logger.exception(f"Failed to download {document.file_name}")
            raise DataAcquisitionError(f"Download failed: {e}") from e
    
    def fetch_from_api(self, job_id: str) -> Dict[str, Any]:
        """Fetch processing status from API.
        
        Args:
            job_id: Job ID to query
            
        Returns:
            API response as dictionary
            
        Raises:
            DataAcquisitionError: If API request fails
        """
        try:
            url = f"{self.config.api_base_url}/api/v1/processing-status/{job_id}"
            headers = {"X-API-Key": self.config.api_key}
            
            response = requests.get(
                url,
                headers=headers,
                timeout=self.config.timeout_seconds
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Fetched job status for {job_id}: {data.get('status')}")
            
            return data
            
        except requests.Timeout as e:
            logger.error(f"API timeout for job {job_id}")
            raise DataAcquisitionError(f"API timeout: {job_id}") from e
        except requests.HTTPError as e:
            logger.error(f"API HTTP error {e.response.status_code}: {e}")
            raise DataAcquisitionError(f"API error: {e.response.status_code}") from e
        except Exception as e:
            logger.exception(f"Unexpected API error for job {job_id}")
            raise DataAcquisitionError(f"API request failed: {e}") from e
    
    def validate_document_format(self, file_path: Path) -> bool:
        """Validate document format and basic properties.
        
        Args:
            file_path: Path to document file
            
        Returns:
            True if valid, False otherwise
        """
        # Check file exists
        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return False
        
        # Check file size (max 50MB)
        file_size = file_path.stat().st_size
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            logger.warning(f"File too large: {file_size} bytes > {max_size} bytes")
            return False
        
        # Check file extension
        valid_extensions = {'.pdf', '.jpeg', '.jpg', '.png', '.tiff', '.tif'}
        if file_path.suffix.lower() not in valid_extensions:
            logger.warning(f"Invalid file extension: {file_path.suffix}")
            return False
        
        logger.info(f"Document validation passed: {file_path.name}")
        return True
    
    def run(self) -> Dict[str, Any]:
        """Run complete data acquisition pipeline.
        
        Returns:
            Dictionary with acquisition statistics
        """
        logger.info("Starting data acquisition pipeline")
        
        stats = {
            "total_documents": 0,
            "downloaded": 0,
            "failed": 0,
            "invalid": 0,
            "start_time": datetime.utcnow().isoformat()
        }
        
        try:
            # Fetch pending documents
            documents = self.fetch_pending_documents()
            stats["total_documents"] = len(documents)
            
            # Download each document
            for doc in documents:
                try:
                    # Download from storage
                    file_path = self.download_from_storage(doc)
                    
                    # Validate format
                    if self.validate_document_format(file_path):
                        stats["downloaded"] += 1
                    else:
                        stats["invalid"] += 1
                        file_path.unlink()  # Delete invalid file
                        
                except DataAcquisitionError as e:
                    logger.error(f"Failed to acquire {doc.file_name}: {e}")
                    stats["failed"] += 1
            
            stats["end_time"] = datetime.utcnow().isoformat()
            logger.info(f"Data acquisition completed: {stats}")
            
            return stats
            
        except Exception as e:
            logger.exception("Data acquisition pipeline failed")
            stats["error"] = str(e)
            stats["end_time"] = datetime.utcnow().isoformat()
            raise DataAcquisitionError(f"Pipeline failed: {e}") from e


def main() -> None:
    """Main entry point for data acquisition script."""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/data_acquisition.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create configuration
    config = DataAcquisitionConfig(
        s3_endpoint=os.getenv("S3_ENDPOINT", "http://localhost:9000"),
        s3_access_key=os.getenv("S3_ACCESS_KEY", "minioadmin"),
        s3_secret_key=os.getenv("S3_SECRET_KEY", "minioadmin123"),
        s3_bucket_name=os.getenv("S3_BUCKET_NAME", "loan-documents"),
        database_url=os.getenv("DATABASE_URL", "postgresql://loanuser:loanpass123@localhost:5432/loanextractor"),
        api_base_url=os.getenv("API_BASE_URL", "http://localhost:8000"),
        api_key=os.getenv("API_KEY", "")
    )
    
    # Run acquisition
    acquisition = DataAcquisition(config)
    stats = acquisition.run()
    
    print(f"\nData Acquisition Summary:")
    print(f"  Total documents: {stats['total_documents']}")
    print(f"  Downloaded: {stats['downloaded']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Invalid: {stats['invalid']}")


if __name__ == "__main__":
    main()
