"""OCR Module for document text extraction"""

from .ocr_engine import OCREngine, OCRResult, HandwritingRecognizer
from .layout_analyzer import LayoutAnalyzer, LayoutStructure, DocumentRegion, RegionType
from .table_extractor import TableExtractor, TableDetector, TableStructure, TableCell, MultiPageTableHandler
from .mixed_content_handler import MixedContentHandler, MixedContent, ContentElement, ContentType
from .multipage_processor import MultiPageProcessor, PageContent, DocumentContent
from .ocr_service import OCRService

__all__ = [
    'OCREngine', 'OCRResult', 'HandwritingRecognizer',
    'LayoutAnalyzer', 'LayoutStructure', 'DocumentRegion', 'RegionType',
    'TableExtractor', 'TableDetector', 'TableStructure', 'TableCell', 'MultiPageTableHandler',
    'MixedContentHandler', 'MixedContent', 'ContentElement', 'ContentType',
    'MultiPageProcessor', 'PageContent', 'DocumentContent',
    'OCRService'
]
