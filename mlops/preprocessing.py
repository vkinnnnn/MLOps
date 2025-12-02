"""Data preprocessing module for document quality checks and standardization.

This module handles:
- Document quality validation
- Format standardization
- Metadata extraction
- Feature engineering
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib

from PIL import Image
import pdf2image
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DocumentQualityMetrics(BaseModel):
    """Quality metrics for a document."""
    
    resolution_dpi: int
    clarity_score: float = Field(..., ge=0.0, le=1.0)
    page_count: int = Field(..., ge=1, le=50)
    file_size_bytes: int = Field(..., gt=0)
    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)


class DocumentFeatures(BaseModel):
    """Extracted features from document."""
    
    document_fingerprint: str
    file_type: str
    page_count: int
    avg_page_size_bytes: int
    creation_timestamp: datetime
    quality_score: float = Field(..., ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PreprocessingConfig(BaseModel):
    """Configuration for preprocessing pipeline."""
    
    input_dir: Path = Field(default=Path("data/raw"))
    output_dir: Path = Field(default=Path("data/processed"))
    min_resolution_dpi: int = Field(default=150, ge=72, le=600)
    max_file_size_mb: int = Field(default=50, ge=1, le=100)
    max_page_count: int = Field(default=50, ge=1, le=100)
    target_format: str = Field(default="pdf", pattern="^(pdf|png)$")


class PreprocessingError(Exception):
    """Custom exception for preprocessing failures."""
    pass


class DocumentPreprocessor:
    """Main class for document preprocessing operations."""
    
    def __init__(self, config: PreprocessingConfig):
        """Initialize preprocessor with configuration.
        
        Args:
            config: PreprocessingConfig instance
        """
        self.config = config
        self.input_dir = config.input_dir
        self.output_dir = config.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("DocumentPreprocessor initialized successfully")
    
    def validate_format(self, file_path: Path) -> bool:
        """Validate document format is supported.
        
        Args:
            file_path: Path to document
            
        Returns:
            True if format is valid, False otherwise
        """
        valid_extensions = {'.pdf', '.jpeg', '.jpg', '.png', '.tiff', '.tif'}
        
        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return False
        
        if file_path.suffix.lower() not in valid_extensions:
            logger.warning(f"Invalid format: {file_path.suffix}")
            return False
        
        return True
    
    def check_quality(self, file_path: Path) -> DocumentQualityMetrics:
        """Perform quality checks on document.
        
        Args:
            file_path: Path to document
            
        Returns:
            DocumentQualityMetrics with quality assessment
            
        Raises:
            PreprocessingError: If quality check fails
        """
        errors = []
        
        try:
            # Check file size
            file_size = file_path.stat().st_size
            max_size = self.config.max_file_size_mb * 1024 * 1024
            
            if file_size > max_size:
                errors.append(f"File size {file_size} exceeds maximum {max_size}")
            
            # Initialize metrics
            resolution_dpi = 300  # Default
            clarity_score = 0.0
            page_count = 1
            
            # Handle different file types
            if file_path.suffix.lower() == '.pdf':
                # Convert PDF to check quality
                try:
                    images = pdf2image.convert_from_path(
                        str(file_path),
                        dpi=150,
                        first_page=1,
                        last_page=1
                    )
                    if images:
                        img = images[0]
                        resolution_dpi = self._estimate_dpi(img)
                        clarity_score = self._calculate_clarity(img)
                    
                    # Get page count
                    all_images = pdf2image.convert_from_path(str(file_path), dpi=50)
                    page_count = len(all_images)
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze PDF quality: {e}")
                    errors.append(f"PDF analysis failed: {e}")
            
            else:
                # Image file
                try:
                    img = Image.open(file_path)
                    resolution_dpi = self._estimate_dpi(img)
                    clarity_score = self._calculate_clarity(img)
                    page_count = 1
                except Exception as e:
                    logger.warning(f"Failed to analyze image quality: {e}")
                    errors.append(f"Image analysis failed: {e}")
            
            # Validate page count
            if page_count > self.config.max_page_count:
                errors.append(f"Page count {page_count} exceeds maximum {self.config.max_page_count}")
            
            # Validate resolution
            if resolution_dpi < self.config.min_resolution_dpi:
                errors.append(f"Resolution {resolution_dpi} DPI below minimum {self.config.min_resolution_dpi}")
            
            # Validate clarity
            if clarity_score < 0.5:
                errors.append(f"Clarity score {clarity_score:.2f} below threshold 0.5")
            
            is_valid = len(errors) == 0
            
            metrics = DocumentQualityMetrics(
                resolution_dpi=resolution_dpi,
                clarity_score=clarity_score,
                page_count=page_count,
                file_size_bytes=file_size,
                is_valid=is_valid,
                validation_errors=errors
            )
            
            logger.info(f"Quality check for {file_path.name}: {'PASS' if is_valid else 'FAIL'}")
            return metrics
            
        except Exception as e:
            logger.exception(f"Quality check failed for {file_path.name}")
            raise PreprocessingError(f"Quality check failed: {e}") from e
    
    def _estimate_dpi(self, img: Image.Image) -> int:
        """Estimate DPI of an image.
        
        Args:
            img: PIL Image object
            
        Returns:
            Estimated DPI
        """
        # Try to get DPI from image info
        dpi = img.info.get('dpi', (300, 300))
        if isinstance(dpi, tuple):
            return int(dpi[0])
        return int(dpi)
    
    def _calculate_clarity(self, img: Image.Image) -> float:
        """Calculate clarity score for an image.
        
        Args:
            img: PIL Image object
            
        Returns:
            Clarity score between 0 and 1
        """
        # Simple clarity metric based on image statistics
        # In production, use more sophisticated metrics like Laplacian variance
        try:
            # Convert to grayscale
            gray = img.convert('L')
            
            # Calculate standard deviation as proxy for clarity
            import numpy as np
            img_array = np.array(gray)
            std_dev = np.std(img_array)
            
            # Normalize to 0-1 range (std_dev typically 0-100 for decent images)
            clarity = min(std_dev / 100.0, 1.0)
            
            return clarity
            
        except Exception as e:
            logger.warning(f"Failed to calculate clarity: {e}")
            return 0.5  # Default moderate clarity
    
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from document.
        
        Args:
            file_path: Path to document
            
        Returns:
            Dictionary of metadata
        """
        try:
            stat = file_path.stat()
            
            metadata = {
                "file_name": file_path.name,
                "file_type": file_path.suffix.lower().lstrip('.'),
                "file_size_bytes": stat.st_size,
                "creation_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modification_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
            
            # Add image-specific metadata
            if file_path.suffix.lower() in ['.jpeg', '.jpg', '.png', '.tiff', '.tif']:
                try:
                    img = Image.open(file_path)
                    metadata.update({
                        "width": img.width,
                        "height": img.height,
                        "mode": img.mode,
                        "format": img.format,
                    })
                except Exception as e:
                    logger.warning(f"Failed to extract image metadata: {e}")
            
            logger.info(f"Extracted metadata for {file_path.name}")
            return metadata
            
        except Exception as e:
            logger.exception(f"Failed to extract metadata for {file_path.name}")
            return {}
    
    def standardize_format(self, file_path: Path) -> Path:
        """Standardize document format for optimal OCR processing.
        
        Args:
            file_path: Path to source document
            
        Returns:
            Path to standardized document
            
        Raises:
            PreprocessingError: If standardization fails
        """
        try:
            output_path = self.output_dir / f"{file_path.stem}_standardized{file_path.suffix}"
            
            # For now, just copy the file
            # In production, implement format conversion logic
            import shutil
            shutil.copy2(file_path, output_path)
            
            logger.info(f"Standardized {file_path.name} -> {output_path.name}")
            return output_path
            
        except Exception as e:
            logger.exception(f"Failed to standardize {file_path.name}")
            raise PreprocessingError(f"Format standardization failed: {e}") from e
    
    def generate_fingerprint(self, file_path: Path) -> str:
        """Generate unique fingerprint for document deduplication.
        
        Args:
            file_path: Path to document
            
        Returns:
            SHA-256 hash of file content
        """
        try:
            sha256_hash = hashlib.sha256()
            
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            fingerprint = sha256_hash.hexdigest()
            logger.info(f"Generated fingerprint for {file_path.name}: {fingerprint[:16]}...")
            
            return fingerprint
            
        except Exception as e:
            logger.exception(f"Failed to generate fingerprint for {file_path.name}")
            return ""
    
    def extract_features(self, file_path: Path) -> DocumentFeatures:
        """Extract all features from document.
        
        Args:
            file_path: Path to document
            
        Returns:
            DocumentFeatures object
            
        Raises:
            PreprocessingError: If feature extraction fails
        """
        try:
            # Get quality metrics
            quality_metrics = self.check_quality(file_path)
            
            # Get metadata
            metadata = self.extract_metadata(file_path)
            
            # Generate fingerprint
            fingerprint = self.generate_fingerprint(file_path)
            
            # Calculate average page size
            avg_page_size = (
                quality_metrics.file_size_bytes // quality_metrics.page_count
                if quality_metrics.page_count > 0
                else quality_metrics.file_size_bytes
            )
            
            features = DocumentFeatures(
                document_fingerprint=fingerprint,
                file_type=metadata.get("file_type", "unknown"),
                page_count=quality_metrics.page_count,
                avg_page_size_bytes=avg_page_size,
                creation_timestamp=datetime.fromisoformat(metadata.get("creation_time", datetime.utcnow().isoformat())),
                quality_score=quality_metrics.clarity_score,
                metadata=metadata
            )
            
            logger.info(f"Extracted features for {file_path.name}")
            return features
            
        except Exception as e:
            logger.exception(f"Failed to extract features from {file_path.name}")
            raise PreprocessingError(f"Feature extraction failed: {e}") from e
    
    def process_document(self, file_path: Path) -> Dict[str, Any]:
        """Process single document through full preprocessing pipeline.
        
        Args:
            file_path: Path to document
            
        Returns:
            Dictionary with processing results
        """
        result = {
            "file_name": file_path.name,
            "success": False,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            # Validate format
            if not self.validate_format(file_path):
                result["error"] = "Invalid format"
                return result
            
            # Check quality
            quality = self.check_quality(file_path)
            if not quality.is_valid:
                result["error"] = f"Quality check failed: {quality.validation_errors}"
                result["quality_metrics"] = quality.model_dump()
                return result
            
            # Extract features
            features = self.extract_features(file_path)
            
            # Standardize format
            standardized_path = self.standardize_format(file_path)
            
            result.update({
                "success": True,
                "quality_metrics": quality.model_dump(),
                "features": features.model_dump(),
                "output_path": str(standardized_path)
            })
            
            logger.info(f"Successfully preprocessed {file_path.name}")
            return result
            
        except Exception as e:
            logger.exception(f"Failed to process {file_path.name}")
            result["error"] = str(e)
            return result
    
    def run(self) -> Dict[str, Any]:
        """Run preprocessing pipeline on all documents in input directory.
        
        Returns:
            Dictionary with processing statistics
        """
        logger.info("Starting preprocessing pipeline")
        
        stats = {
            "total_documents": 0,
            "processed": 0,
            "failed": 0,
            "invalid": 0,
            "start_time": datetime.utcnow().isoformat()
        }
        
        try:
            # Get all documents
            documents = list(self.input_dir.glob("*.*"))
            stats["total_documents"] = len(documents)
            
            # Process each document
            for doc_path in documents:
                result = self.process_document(doc_path)
                
                if result["success"]:
                    stats["processed"] += 1
                elif "Quality check failed" in result.get("error", ""):
                    stats["invalid"] += 1
                else:
                    stats["failed"] += 1
            
            stats["end_time"] = datetime.utcnow().isoformat()
            logger.info(f"Preprocessing completed: {stats}")
            
            return stats
            
        except Exception as e:
            logger.exception("Preprocessing pipeline failed")
            stats["error"] = str(e)
            stats["end_time"] = datetime.utcnow().isoformat()
            raise PreprocessingError(f"Pipeline failed: {e}") from e


def main() -> None:
    """Main entry point for preprocessing script."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/preprocessing.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create configuration
    config = PreprocessingConfig()
    
    # Run preprocessing
    preprocessor = DocumentPreprocessor(config)
    stats = preprocessor.run()
    
    print(f"\nPreprocessing Summary:")
    print(f"  Total documents: {stats['total_documents']}")
    print(f"  Processed: {stats['processed']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Invalid: {stats['invalid']}")


if __name__ == "__main__":
    main()
