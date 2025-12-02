"""
Document metadata extraction module.
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import hashlib
from PIL import Image
import PyPDF2


class DocumentMetadataExtractor:
    """Extracts and manages document metadata."""
    
    def __init__(self):
        """Initialize the metadata extractor."""
        pass
    
    def extract_metadata(
        self, 
        file_path: str,
        file_name: str,
        file_type: str,
        page_count: int
    ) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from a document.
        
        Args:
            file_path: Path to the document file
            file_name: Original filename
            file_type: Type of file (pdf, jpeg, png, tiff)
            page_count: Number of pages in the document
            
        Returns:
            Dictionary containing document metadata
        """
        # Generate unique document ID
        document_id = self.generate_document_id()
        
        # Get file statistics
        file_stats = os.stat(file_path)
        file_size = file_stats.st_size
        
        # Get upload timestamp
        upload_timestamp = datetime.now()
        
        # Calculate file hash for integrity verification
        file_hash = self._calculate_file_hash(file_path)
        
        # Extract additional format-specific metadata
        additional_metadata = self._extract_format_specific_metadata(file_path, file_type)
        
        # Compile metadata
        metadata = {
            "document_id": document_id,
            "file_name": file_name,
            "file_type": file_type,
            "file_size_bytes": file_size,
            "page_count": page_count,
            "upload_timestamp": upload_timestamp.isoformat(),
            "file_hash": file_hash,
            "storage_path": file_path,
            **additional_metadata
        }
        
        return metadata
    
    def generate_document_id(self) -> str:
        """
        Generate a unique document ID.
        
        Returns:
            UUID string as document identifier
        """
        return str(uuid.uuid4())
    
    def _calculate_file_hash(self, file_path: str, algorithm: str = 'sha256') -> str:
        """
        Calculate hash of file for integrity verification.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm to use (default: sha256)
            
        Returns:
            Hexadecimal hash string
        """
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    def _extract_format_specific_metadata(
        self, 
        file_path: str, 
        file_type: str
    ) -> Dict[str, Any]:
        """
        Extract format-specific metadata.
        
        Args:
            file_path: Path to the document
            file_type: Type of file
            
        Returns:
            Dictionary with format-specific metadata
        """
        metadata = {}
        
        try:
            if file_type == 'pdf':
                metadata.update(self._extract_pdf_metadata(file_path))
            elif file_type in ['jpeg', 'png', 'tiff']:
                metadata.update(self._extract_image_metadata(file_path))
        except Exception as e:
            # If metadata extraction fails, log but don't fail the entire process
            metadata['metadata_extraction_error'] = str(e)
        
        return metadata
    
    def _extract_pdf_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract metadata from PDF files.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with PDF metadata
        """
        metadata = {}
        
        try:
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                # Get PDF info
                if pdf_reader.metadata:
                    pdf_info = pdf_reader.metadata
                    
                    # Extract common metadata fields
                    metadata['pdf_title'] = pdf_info.get('/Title', None)
                    metadata['pdf_author'] = pdf_info.get('/Author', None)
                    metadata['pdf_subject'] = pdf_info.get('/Subject', None)
                    metadata['pdf_creator'] = pdf_info.get('/Creator', None)
                    metadata['pdf_producer'] = pdf_info.get('/Producer', None)
                    
                    # Extract creation and modification dates
                    if '/CreationDate' in pdf_info:
                        metadata['pdf_creation_date'] = str(pdf_info['/CreationDate'])
                    if '/ModDate' in pdf_info:
                        metadata['pdf_modification_date'] = str(pdf_info['/ModDate'])
                
                # Check if PDF is encrypted
                metadata['pdf_encrypted'] = pdf_reader.is_encrypted
                
        except Exception as e:
            metadata['pdf_metadata_error'] = str(e)
        
        return metadata
    
    def _extract_image_metadata(self, image_path: str) -> Dict[str, Any]:
        """
        Extract metadata from image files.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with image metadata
        """
        metadata = {}
        
        try:
            with Image.open(image_path) as img:
                # Get image dimensions
                metadata['image_width'] = img.width
                metadata['image_height'] = img.height
                
                # Get image mode (RGB, RGBA, L, etc.)
                metadata['image_mode'] = img.mode
                
                # Get image format
                metadata['image_format'] = img.format
                
                # Get DPI if available
                if 'dpi' in img.info:
                    metadata['image_dpi'] = img.info['dpi']
                
                # For TIFF, check if multi-page
                if hasattr(img, 'n_frames'):
                    metadata['image_frames'] = img.n_frames
                
                # Extract EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    exif_data = img._getexif()
                    if exif_data:
                        metadata['has_exif'] = True
                        # Extract some common EXIF fields
                        metadata['exif_datetime'] = exif_data.get(306, None)  # DateTime
                        metadata['exif_make'] = exif_data.get(271, None)  # Make
                        metadata['exif_model'] = exif_data.get(272, None)  # Model
                
        except Exception as e:
            metadata['image_metadata_error'] = str(e)
        
        return metadata
    
    def create_metadata_summary(self, metadata: Dict[str, Any]) -> str:
        """
        Create a human-readable summary of document metadata.
        
        Args:
            metadata: Document metadata dictionary
            
        Returns:
            Formatted string summary
        """
        summary_lines = [
            f"Document ID: {metadata['document_id']}",
            f"File Name: {metadata['file_name']}",
            f"File Type: {metadata['file_type'].upper()}",
            f"File Size: {self._format_file_size(metadata['file_size_bytes'])}",
            f"Page Count: {metadata['page_count']}",
            f"Upload Time: {metadata['upload_timestamp']}",
        ]
        
        # Add format-specific info
        if metadata['file_type'] == 'pdf' and 'pdf_title' in metadata and metadata['pdf_title']:
            summary_lines.append(f"PDF Title: {metadata['pdf_title']}")
        
        if 'image_width' in metadata and 'image_height' in metadata:
            summary_lines.append(
                f"Image Dimensions: {metadata['image_width']}x{metadata['image_height']}"
            )
        
        return "\n".join(summary_lines)
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: File size in bytes
            
        Returns:
            Formatted string (e.g., "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
