"""
Multi-page Document Processor Module

Processes documents sequentially page by page, maintains context across
page boundaries, and combines multi-page tables.
Includes parallel processing optimization for multi-page documents.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from PIL import Image
import cv2
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import hashlib
from functools import lru_cache
import pickle

from .ocr_engine import OCREngine, OCRResult
from .layout_analyzer import LayoutAnalyzer, LayoutStructure
from .table_extractor import TableExtractor, TableStructure, MultiPageTableHandler
from .mixed_content_handler import MixedContentHandler, MixedContent


@dataclass
class PageContent:
    """Container for single page content"""
    page_number: int
    ocr_result: OCRResult
    layout: LayoutStructure
    tables: List[TableStructure]
    mixed_content: MixedContent


@dataclass
class DocumentContent:
    """Container for complete document content"""
    pages: List[PageContent]
    total_pages: int
    combined_text: str
    all_tables: List[TableStructure]
    document_metadata: Dict[str, any]


class MultiPageProcessor:
    """
    Processes multi-page documents with parallel processing optimization
    """
    
    def __init__(self, enable_parallel: bool = True, max_workers: Optional[int] = None):
        """
        Initialize multi-page processor
        
        Args:
            enable_parallel: Enable parallel processing for pages
            max_workers: Maximum number of worker threads (None = auto)
        """
        self.ocr_engine = OCREngine()
        self.layout_analyzer = LayoutAnalyzer()
        self.table_extractor = TableExtractor()
        self.mixed_content_handler = MixedContentHandler()
        self.multipage_table_handler = MultiPageTableHandler()
        
        self.max_pages = 50  # Maximum pages to process
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers
        
        # Cache for OCR results
        self._ocr_cache = {}
    
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
    
    def _get_cached_ocr_result(self, image: np.ndarray) -> Optional[OCRResult]:
        """
        Get cached OCR result if available
        
        Args:
            image: Image to check
            
        Returns:
            Cached OCRResult or None
        """
        image_hash = self._get_image_hash(image)
        return self._ocr_cache.get(image_hash)
    
    def _cache_ocr_result(self, image: np.ndarray, result: OCRResult):
        """
        Cache OCR result
        
        Args:
            image: Image that was processed
            result: OCR result to cache
        """
        image_hash = self._get_image_hash(image)
        self._ocr_cache[image_hash] = result
    
    def process_document(self, pages: List[np.ndarray]) -> DocumentContent:
        """
        Process multi-page document with parallel processing
        
        Args:
            pages: List of page images as numpy arrays
            
        Returns:
            DocumentContent containing all extracted information
        """
        if len(pages) > self.max_pages:
            raise ValueError(f"Document exceeds maximum page limit of {self.max_pages}")
        
        if self.enable_parallel and len(pages) > 1:
            page_contents = self._process_pages_parallel(pages)
        else:
            page_contents = self._process_pages_sequential(pages)
        
        # Combine text from all pages
        all_text = [page.ocr_result.text for page in page_contents]
        combined_text = "\n\n--- Page Break ---\n\n".join(all_text)
        
        # Combine multi-page tables
        all_tables = self._combine_tables_across_pages(page_contents)
        
        # Create document metadata
        metadata = self._create_document_metadata(page_contents)
        
        return DocumentContent(
            pages=page_contents,
            total_pages=len(pages),
            combined_text=combined_text,
            all_tables=all_tables,
            document_metadata=metadata
        )
    
    def _process_pages_sequential(self, pages: List[np.ndarray]) -> List[PageContent]:
        """
        Process pages sequentially (original method)
        
        Args:
            pages: List of page images
            
        Returns:
            List of PageContent objects
        """
        page_contents = []
        for page_num, page_image in enumerate(pages, start=1):
            page_content = self._process_page(page_image, page_num)
            page_contents.append(page_content)
        return page_contents
    
    def _process_pages_parallel(self, pages: List[np.ndarray]) -> List[PageContent]:
        """
        Process pages in parallel for improved performance
        
        Args:
            pages: List of page images
            
        Returns:
            List of PageContent objects in correct order
        """
        page_contents = [None] * len(pages)
        
        # Use ThreadPoolExecutor for I/O-bound OCR operations
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all pages for processing
            future_to_page = {
                executor.submit(self._process_page, page_image, page_num): page_num - 1
                for page_num, page_image in enumerate(pages, start=1)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_page):
                page_index = future_to_page[future]
                try:
                    page_content = future.result()
                    page_contents[page_index] = page_content
                except Exception as exc:
                    print(f'Page {page_index + 1} generated an exception: {exc}')
                    # Create empty page content on error
                    page_contents[page_index] = self._create_empty_page_content(page_index + 1)
        
        return page_contents
    
    def _create_empty_page_content(self, page_number: int) -> PageContent:
        """
        Create empty page content for error cases
        
        Args:
            page_number: Page number
            
        Returns:
            Empty PageContent
        """
        return PageContent(
            page_number=page_number,
            ocr_result=OCRResult(text="", confidence=0.0, word_confidences=[], bounding_boxes=[]),
            layout=LayoutStructure(text_blocks=[], headers=[], tables=[], images=[]),
            tables=[],
            mixed_content=MixedContent(text_segments=[], numbers=[], special_chars=[])
        )
    
    def _process_page(self, page_image: np.ndarray, page_number: int) -> PageContent:
        """
        Process a single page with caching
        
        Args:
            page_image: Page image as numpy array
            page_number: Page number (1-indexed)
            
        Returns:
            PageContent for this page
        """
        # Check cache first
        cached_result = self._get_cached_ocr_result(page_image)
        
        if cached_result is not None:
            ocr_result = cached_result
        else:
            # Preprocess image for better OCR
            preprocessed = self.ocr_engine.preprocess_for_ocr(page_image)
            
            # Extract text with OCR
            ocr_result = self.ocr_engine.extract_text(preprocessed)
            
            # Cache the result
            self._cache_ocr_result(page_image, ocr_result)
        
        # Analyze layout
        layout = self.layout_analyzer.analyze_layout(page_image)
        
        # Extract tables
        tables = self.table_extractor.extract_tables(page_image, use_ocr=True)
        
        # Mark page number on tables
        for table in tables:
            table.page_number = page_number
        
        # Extract mixed content
        mixed_content = self.mixed_content_handler.extract_mixed_content(ocr_result.text)
        
        return PageContent(
            page_number=page_number,
            ocr_result=ocr_result,
            layout=layout,
            tables=tables,
            mixed_content=mixed_content
        )
    
    def _combine_tables_across_pages(self, page_contents: List[PageContent]) -> List[TableStructure]:
        """
        Combine tables that span multiple pages
        
        Args:
            page_contents: List of PageContent objects
            
        Returns:
            List of combined tables
        """
        # Collect all tables from all pages
        all_tables = []
        for page_content in page_contents:
            all_tables.extend(page_content.tables)
        
        # Use MultiPageTableHandler to combine tables
        combined_tables = self.multipage_table_handler.combine_multipage_tables(all_tables)
        
        return combined_tables
    
    def maintain_context_across_pages(self, page_contents: List[PageContent]) -> Dict[str, any]:
        """
        Maintain context across page boundaries
        
        Args:
            page_contents: List of PageContent objects
            
        Returns:
            Dictionary containing cross-page context information
        """
        context = {
            'page_transitions': [],
            'continued_sections': [],
            'cross_page_references': []
        }
        
        # Analyze page transitions
        for i in range(len(page_contents) - 1):
            current_page = page_contents[i]
            next_page = page_contents[i + 1]
            
            # Check if content continues across pages
            transition_info = self._analyze_page_transition(current_page, next_page)
            context['page_transitions'].append(transition_info)
        
        return context
    
    def _analyze_page_transition(self, page1: PageContent, page2: PageContent) -> Dict[str, any]:
        """
        Analyze transition between two consecutive pages
        
        Args:
            page1: First page content
            page2: Second page content
            
        Returns:
            Dictionary with transition information
        """
        transition = {
            'from_page': page1.page_number,
            'to_page': page2.page_number,
            'has_continued_table': False,
            'has_continued_text': False
        }
        
        # Check for continued tables
        if page1.tables and page2.tables:
            # Simple heuristic: if last table on page1 and first table on page2 have same headers
            last_table = page1.tables[-1]
            first_table = page2.tables[0]
            if last_table.headers == first_table.headers:
                transition['has_continued_table'] = True
        
        # Check for continued text (sentence ends on next page)
        page1_text = page1.ocr_result.text.strip()
        if page1_text and not page1_text.endswith(('.', '!', '?')):
            transition['has_continued_text'] = True
        
        return transition
    
    def _create_document_metadata(self, page_contents: List[PageContent]) -> Dict[str, any]:
        """
        Create metadata for the entire document
        
        Args:
            page_contents: List of PageContent objects
            
        Returns:
            Dictionary containing document metadata
        """
        # Calculate average confidence across all pages
        total_confidence = sum(page.ocr_result.confidence for page in page_contents)
        avg_confidence = total_confidence / len(page_contents) if page_contents else 0.0
        
        # Count total tables
        total_tables = sum(len(page.tables) for page in page_contents)
        
        # Count total text blocks
        total_text_blocks = sum(len(page.layout.text_blocks) for page in page_contents)
        
        metadata = {
            'total_pages': len(page_contents),
            'average_ocr_confidence': avg_confidence,
            'total_tables': total_tables,
            'total_text_blocks': total_text_blocks,
            'page_confidences': [page.ocr_result.confidence for page in page_contents],
            'parallel_processing_enabled': self.enable_parallel
        }
        
        return metadata
    
    def extract_page_range(self, pages: List[np.ndarray], start_page: int, end_page: int) -> DocumentContent:
        """
        Process a specific range of pages
        
        Args:
            pages: List of all page images
            start_page: Starting page number (1-indexed)
            end_page: Ending page number (1-indexed, inclusive)
            
        Returns:
            DocumentContent for the specified page range
        """
        # Validate page range
        if start_page < 1 or end_page > len(pages) or start_page > end_page:
            raise ValueError(f"Invalid page range: {start_page}-{end_page}")
        
        # Extract page range (convert to 0-indexed)
        page_range = pages[start_page-1:end_page]
        
        return self.process_document(page_range)
    
    def clear_cache(self):
        """Clear the OCR cache"""
        self._ocr_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        return {
            'cache_size': len(self._ocr_cache),
            'cache_entries': len(self._ocr_cache)
        }
