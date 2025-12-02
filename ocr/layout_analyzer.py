"""
Layout Analysis Module

Identifies document structure including text blocks, headers, tables, and regions.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class RegionType(Enum):
    """Types of document regions"""
    TEXT = "text"
    HEADER = "header"
    TABLE = "table"
    IMAGE = "image"
    FOOTER = "footer"
    SIGNATURE = "signature"


@dataclass
class DocumentRegion:
    """Represents a region in the document"""
    region_type: RegionType
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    confidence: float
    text_content: Optional[str] = None


@dataclass
class LayoutStructure:
    """Container for document layout analysis results"""
    regions: List[DocumentRegion]
    page_width: int
    page_height: int
    text_blocks: List[DocumentRegion]
    headers: List[DocumentRegion]
    tables: List[DocumentRegion]


class LayoutAnalyzer:
    """
    Analyzes document layout to identify structure and regions
    """
    
    def __init__(self):
        """Initialize layout analyzer"""
        self.min_text_height = 10
        self.min_text_width = 20
    
  
  def analyze_layout(self, image: np.ndarray) -> LayoutStructure:
        """
        Analyze document layout and identify regions
        
        Args:
            image: Input document image as numpy array
            
        Returns:
            LayoutStructure containing identified regions
        """
        height, width = image.shape[:2]
        
        # Detect all regions
        regions = self._detect_regions(image)
        
        # Classify regions
        text_blocks = [r for r in regions if r.region_type == RegionType.TEXT]
        headers = [r for r in regions if r.region_type == RegionType.HEADER]
        tables = [r for r in regions if r.region_type == RegionType.TABLE]
        
        return LayoutStructure(
            regions=regions,
            page_width=width,
            page_height=height,
            text_blocks=text_blocks,
            headers=headers,
            tables=tables
        )
    
    def _detect_regions(self, image: np.ndarray) -> List[DocumentRegion]:
        """
        Detect document regions using contour detection
        
        Args:
            image: Input image
            
        Returns:
            List of detected regions
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply binary threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
   
     
        # Dilate to connect nearby text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
        dilated = cv2.dilate(binary, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        regions = []
        height, width = image.shape[:2]
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter out very small regions
            if w < self.min_text_width or h < self.min_text_height:
                continue
            
            # Classify region type
            region_type = self._classify_region(x, y, w, h, width, height)
            
            # Calculate confidence (simplified)
            confidence = 0.8
            
            region = DocumentRegion(
                region_type=region_type,
                bbox=(x, y, w, h),
                confidence=confidence
            )
            regions.append(region)
        
        # Sort regions by vertical position (top to bottom)
        regions.sort(key=lambda r: r.bbox[1])
        
        return regions
    
    def _classify_region(self, x: int, y: int, w: int, h: int, 
                        page_width: int, page_height: int) -> RegionType:
        """
        Classify region type based on position and dimensions
        
        Args:
            x, y, w, h: Region bounding box
            page_width, page_height: Page dimensions
            
        Returns:
            RegionType classification
        """
        # Header detection: top 15% of page, wide region
        if y < page_height * 0.15 and w > page_width * 0.5:
            return RegionType.HEADER
  
      
        # Footer detection: bottom 10% of page
        if y > page_height * 0.9:
            return RegionType.FOOTER
        
        # Table detection: rectangular region with specific aspect ratio
        aspect_ratio = w / h if h > 0 else 0
        if 2 < aspect_ratio < 10 and w > page_width * 0.4:
            return RegionType.TABLE
        
        # Default to text block
        return RegionType.TEXT
    
    def identify_text_blocks(self, image: np.ndarray) -> List[DocumentRegion]:
        """
        Identify text blocks in document
        
        Args:
            image: Input image
            
        Returns:
            List of text block regions
        """
        layout = self.analyze_layout(image)
        return layout.text_blocks
    
    def identify_headers(self, image: np.ndarray) -> List[DocumentRegion]:
        """
        Identify header regions in document
        
        Args:
            image: Input image
            
        Returns:
            List of header regions
        """
        layout = self.analyze_layout(image)
        return layout.headers
    
    def detect_sections(self, image: np.ndarray) -> Dict[str, List[DocumentRegion]]:
        """
        Detect and classify document sections
        
        Args:
            image: Input image
            
        Returns:
            Dictionary mapping section names to regions
        """
        layout = self.analyze_layout(image)
        
        sections = {
            'headers': layout.headers,
            'text_blocks': layout.text_blocks,
            'tables': layout.tables,
            'other': [r for r in layout.regions 
                     if r.region_type not in [RegionType.HEADER, RegionType.TEXT, RegionType.TABLE]]
        }
        
        return sections
