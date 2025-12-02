"""
Document ingestion and upload handling for loan documents.

This module provides functionality to upload, validate, and preprocess
loan documents in various formats (PDF, JPEG, PNG, TIFF).
"""

import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import io
from PIL import Image

try:
    import PyPDF2  # type: ignore
except Exception:  # ImportError or other issues loading optional dependency
    PyPDF2 = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised for document validation errors."""
    pass


class DocumentMetadata:
    """Metadata for uploaded documents."""
    
    def __init__(
        self,
        document_id: str,
        file_name: str,
        file_type: str,
        file_size_bytes: int,
        page_count: int,
        upload_timestamp: datetime
    ):
        self.document_id = document_id
        self.file_name = file_name
        self.file_type = file_type
        self.file_size_bytes = file_size_bytes
        self.page_count = page_count
        self.upload_timestamp = upload_timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            'document_id': self.document_id,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'file_size_bytes': self.file_size_bytes,
            'page_count': self.page_count,
            'upload_timestamp': self.upload_timestamp.isoformat()
        }


class DocumentUploadHandler:
    """
    Handler for document upload and validation.
    
    Validates file formats, extracts metadata, and prepares documents
    for processing.
    """
    
    # Supported file types
    SUPPORTED_TYPES = {
        'application/pdf': '.pdf',
        'image/jpeg': '.jpg',
        'image/jpg': '.jpg',
        'image/png': '.png',
        'image/tiff': '.tiff',
        'image/tif': '.tif'
    }
    
    # Maximum file size (50 MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    def __init__(self):
        """Initialize document upload handler."""
        logger.info("DocumentUploadHandler initialized")
    
    def upload_document(
        self,
        file_data: bytes,
        file_name: str,
        content_type: Optional[str] = None
    ) -> DocumentMetadata:
        """
        Upload and validate a document.
        
        Args:
            file_data: Binary file content
            file_name: Name of the file
            content_type: MIME type of the file
        
        Returns:
            DocumentMetadata with document information
        
        Raises:
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Uploading document: {file_name}")
            
            # Validate file size
            file_size = len(file_data)
            if file_size > self.MAX_FILE_SIZE:
                raise ValidationError(
                    f"File size ({file_size} bytes) exceeds maximum allowed size ({self.MAX_FILE_SIZE} bytes)"
                )
            
            # Detect content type if not provided
            if not content_type:
                content_type = self._detect_content_type(file_name, file_data)
            
            # Validate file type
            if content_type not in self.SUPPORTED_TYPES:
                raise ValidationError(
                    f"Unsupported file type: {content_type}. "
                    f"Supported types: {', '.join(self.SUPPORTED_TYPES.keys())}"
                )
            
            # Count pages
            page_count = self._count_pages(file_data, content_type)
            
            # Generate document ID
            document_id = str(uuid.uuid4())
            
            # Create metadata
            metadata = DocumentMetadata(
                document_id=document_id,
                file_name=file_name,
                file_type=content_type,
                file_size_bytes=file_size,
                page_count=page_count,
                upload_timestamp=datetime.now()
            )
            
            logger.info(f"Document uploaded successfully: {document_id}")
            
            return metadata
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            raise ValidationError(f"Failed to upload document: {str(e)}")
    
    def upload_document_from_path(self, file_path: str) -> DocumentMetadata:
        """
        Upload a document from file path.
        
        Args:
            file_path: Path to the document file
        
        Returns:
            DocumentMetadata with document information
        
        Raises:
            ValidationError: If validation fails
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                raise ValidationError(f"File not found: {file_path}")
            
            # Read file content
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Detect content type from extension
            content_type = self._detect_content_type_from_extension(path.suffix)
            
            return self.upload_document(file_data, path.name, content_type)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Upload from path error: {str(e)}")
            raise ValidationError(f"Failed to upload document from path: {str(e)}")
    
    def validate_format(self, file_data: bytes, content_type: str) -> bool:
        """
        Validate document format.
        
        Args:
            file_data: Binary file content
            content_type: MIME type
        
        Returns:
            True if valid, False otherwise
        """
        try:
            if content_type == 'application/pdf':
                # Try to read PDF (requires optional PyPDF2 dependency)
                if PyPDF2 is None:
                    raise ValidationError("PDF validation requires PyPDF2. Please install it to upload PDFs.")
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
                return len(pdf_reader.pages) > 0

            elif content_type.startswith('image/'):
                # Try to open image
                image = Image.open(io.BytesIO(file_data))
                return image.size[0] > 0 and image.size[1] > 0
            
            return False
            
        except Exception as e:
            logger.warning(f"Format validation failed: {str(e)}")
            return False
    
    def _detect_content_type(self, file_name: str, file_data: bytes) -> str:
        """Detect content type from file name and data."""
        # Try extension first
        ext = Path(file_name).suffix.lower()
        content_type = self._detect_content_type_from_extension(ext)
        
        if content_type:
            return content_type
        
        # Try to detect from file data
        if file_data[:4] == b'%PDF':
            return 'application/pdf'
        elif file_data[:2] == b'\xff\xd8':
            return 'image/jpeg'
        elif file_data[:8] == b'\x89PNG\r\n\x1a\n':
            return 'image/png'
        elif file_data[:2] in (b'II', b'MM'):
            return 'image/tiff'
        
        raise ValidationError("Could not detect file type")
    
    def _detect_content_type_from_extension(self, extension: str) -> Optional[str]:
        """Detect content type from file extension."""
        ext_map = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff'
        }
        return ext_map.get(extension.lower())
    
    def _count_pages(self, file_data: bytes, content_type: str) -> int:
        """Count pages in document."""
        try:
            if content_type == 'application/pdf':
                if PyPDF2 is None:
                    # Without PyPDF2 we can't accurately count pages; treat as single-page PDF
                    logger.warning("PyPDF2 not available; assuming single-page PDF for page count.")
                    return 1
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
                return len(pdf_reader.pages)
            else:
                # Images are single page
                return 1
        except Exception as e:
            logger.warning(f"Could not count pages: {str(e)}")
            return 1


class ProcessedDocument:
    """Represents a preprocessed document ready for OCR."""
    
    def __init__(
        self,
        document_id: str,
        file_data: bytes,
        content_type: str,
        page_count: int
    ):
        self.document_id = document_id
        self.file_data = file_data
        self.content_type = content_type
        self.page_count = page_count


class DocumentPreprocessor:
    """
    Preprocessor for optimizing documents for OCR.
    
    Handles image enhancement, format conversion, and optimization.
    """
    
    def __init__(self):
        """Initialize document preprocessor."""
        logger.info("DocumentPreprocessor initialized")
    
    def preprocess_document(
        self,
        file_data: bytes,
        content_type: str,
        document_id: str
    ) -> ProcessedDocument:
        """
        Preprocess document for OCR.
        
        Args:
            file_data: Binary file content
            content_type: MIME type
            document_id: Document identifier
        
        Returns:
            ProcessedDocument ready for OCR
        """
        try:
            logger.info(f"Preprocessing document: {document_id}")
            
            # For now, pass through without modification
            # In production, this would handle image enhancement, etc.
            
            # Count pages
            page_count = 1
            if content_type == 'application/pdf':
                try:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
                    page_count = len(pdf_reader.pages)
                except:
                    pass
            
            processed = ProcessedDocument(
                document_id=document_id,
                file_data=file_data,
                content_type=content_type,
                page_count=page_count
            )
            
            logger.info(f"Document preprocessed: {document_id}")
            
            return processed
            
        except Exception as e:
            logger.error(f"Preprocessing error: {str(e)}")
            raise
