"""
OCR Service Module

High-level service that integrates all OCR components for document processing.
Includes caching for improved performance.
"""

import numpy as np
from typing import List, Dict, Optional
from pathlib import Path
import hashlib
from functools import lru_cache

from .ocr_engine import OCREngine, OCRResult
from .layout_analyzer import LayoutAnalyzer, LayoutStructure
from .table_extractor import TableExtractor, TableStructure
from .mixed_content_handler import MixedContentHandler, MixedContent
from .multipage_processor import MultiPageProcessor, DocumentContent


class OCRService:
    """
    High-level OCR service integrating all OCR components with caching
    """
    
    def __init__(self, tesseract_cmd: Optional[str] = None, enable_cache: bool = True, enable_parallel: bool = True):
        """
        Initialize OCR service
        
        Args:
            tesseract_cmd: Path to tesseract executable (optional)
            enable_cache: Enable result caching for repeated operations
            enable_parallel: Enable parallel processing for multi-page documents
        """
        self.ocr_engine = OCREngine(tesseract_cmd)
        self.layout_analyzer = LayoutAnalyzer()
        self.table_extractor = TableExtractor()
        self.mixed_content_handler = MixedContentHandler()
        self.multipage_processor = MultiPageProcessor(enable_parallel=enable_parallel)
        
        self.enable_cache = enable_cache
        self._result_cache = {}
    
    def _get_image_hash(self, image: np.ndarray) -> str:
        """
        Generate hash for image to use as cache key
        
        Args:
            image: Image as numpy array
            
        Returns:
            Hash string
        """
        # Use a subset of pixels for faster hashing
        sample = image[::10, ::10].tobytes()
        return hashlib.md5(sample).hexdigest()
    
    def _get_cached_result(self, image: np.ndarray, operation: str) -> Optional[Dict]:
        """
        Get cached result if available
        
        Args:
            image: Image to check
            operation: Operation type (e.g., 'single_page', 'text_only')
            
        Returns:
            Cached result or None
        """
        if not self.enable_cache:
            return None
        
        cache_key = f"{self._get_image_hash(image)}_{operation}"
        return self._result_cache.get(cache_key)
    
    def _cache_result(self, image: np.ndarray, operation: str, result: Dict):
        """
        Cache operation result
        
        Args:
            image: Image that was processed
            operation: Operation type
            result: Result to cache
        """
        if not self.enable_cache:
            return
        
        cache_key = f"{self._get_image_hash(image)}_{operation}"
        self._result_cache[cache_key] = result
    
    def process_single_page(self, image: np.ndarray) -> Dict[str, any]:
        """
        Process a single page document with caching
        
        Args:
            image: Page image as numpy array
            
        Returns:
            Dictionary containing all extracted information
        """
        # Check cache first
        cached = self._get_cached_result(image, 'single_page')
        if cached is not None:
            return cached
        
        # Preprocess image
        preprocessed = self.ocr_engine.preprocess_for_ocr(image)
        
        # Extract text
        ocr_result = self.ocr_engine.extract_text(preprocessed)
        
        # Analyze layout
        layout = self.layout_analyzer.analyze_layout(image)
        
        # Extract tables
        tables = self.table_extractor.extract_tables(image, use_ocr=True)
        
        # Extract mixed content
        mixed_content = self.mixed_content_handler.extract_mixed_content(ocr_result.text)
        
        result = {
            'text': ocr_result.text,
            'confidence': ocr_result.confidence,
            'layout': layout,
            'tables': tables,
            'mixed_content': mixed_content,
            'word_confidences': ocr_result.word_confidences
        }
        
        # Cache the result
        self._cache_result(image, 'single_page', result)
        
        return result
    
    def process_multipage_document(self, pages: List[np.ndarray]) -> DocumentContent:
        """
        Process a multi-page document with parallel processing
        
        Args:
            pages: List of page images as numpy arrays
            
        Returns:
            DocumentContent containing all extracted information
        """
        return self.multipage_processor.process_document(pages)
    
    def extract_text_only(self, image: np.ndarray) -> str:
        """
        Extract only text from image (quick extraction) with caching
        
        Args:
            image: Input image
            
        Returns:
            Extracted text string
        """
        # Check cache first
        cached = self._get_cached_result(image, 'text_only')
        if cached is not None:
            return cached['text']
        
        preprocessed = self.ocr_engine.preprocess_for_ocr(image)
        result = self.ocr_engine.extract_text(preprocessed)
        
        # Cache the result
        self._cache_result(image, 'text_only', {'text': result.text})
        
        return result.text
    
    def extract_tables_only(self, image: np.ndarray) -> List[TableStructure]:
        """
        Extract only tables from image with caching
        
        Args:
            image: Input image
            
        Returns:
            List of extracted tables
        """
        # Check cache first
        cached = self._get_cached_result(image, 'tables_only')
        if cached is not None:
            return cached['tables']
        
        tables = self.table_extractor.extract_tables(image, use_ocr=True)
        
        # Cache the result
        self._cache_result(image, 'tables_only', {'tables': tables})
        
        return tables
    
    def get_document_structure(self, image: np.ndarray) -> LayoutStructure:
        """
        Get document structure without text extraction with caching
        
        Args:
            image: Input image
            
        Returns:
            LayoutStructure containing document regions
        """
        # Check cache first
        cached = self._get_cached_result(image, 'structure_only')
        if cached is not None:
            return cached['layout']
        
        layout = self.layout_analyzer.analyze_layout(image)
        
        # Cache the result
        self._cache_result(image, 'structure_only', {'layout': layout})
        
        return layout
    
    def clear_cache(self):
        """Clear all caches"""
        self._result_cache.clear()
        self.multipage_processor.clear_cache()
    
    def get_cache_stats(self) -> Dict[str, any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        return {
            'service_cache_size': len(self._result_cache),
            'multipage_cache_stats': self.multipage_processor.get_cache_stats(),
            'cache_enabled': self.enable_cache
        }
