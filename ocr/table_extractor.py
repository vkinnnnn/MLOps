"""
Table Detection and Extraction Module

Detects and extracts table structures from documents using Camelot and Tabula.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import tempfile
import os
from PIL import Image


@dataclass
class TableCell:
    """Represents a single table cell"""
    row: int
    col: int
    text: str
    bbox: Tuple[int, int, int, int]


@dataclass
class TableStructure:
    """Represents extracted table structure"""
    headers: List[str]
    rows: List[List[str]]
    cells: List[TableCell]
    bbox: Tuple[int, int, int, int]
    nested_columns: Optional[Dict[str, List[str]]] = None
    page_number: int = 0


class TableDetector:
    """
    Detects tables in document images using contour-based detection
    """
    
    def __init__(self):
        """Initialize table detector"""
        self.min_table_width = 100
        self.min_table_height = 50
    
    def detect_tables(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect table regions in image
        
        Args:
            image: Input image as numpy array
           
 
        Returns:
            List of bounding boxes (x, y, width, height) for detected tables
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply binary threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Detect horizontal and vertical lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        
        horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
        vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
        
        # Combine lines to detect table structure
        table_mask = cv2.add(horizontal_lines, vertical_lines)
        
        # Dilate to connect nearby lines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        table_mask = cv2.dilate(table_mask, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        table_bboxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by minimum size
            if w >= self.min_table_width and h >= self.min_table_height:
                table_bboxes.append((x, y, w, h))
        
        return table_bboxes


class TableExtractor:
    """
    Extracts table data from detected table regions
    """
    
    def __init__(self):
        """Initialize table extractor"""
        self.detector = TableDetector()
  
  
    def extract_tables(self, image: np.ndarray, use_ocr: bool = True) -> List[TableStructure]:
        """
        Extract table structures from image
        
        Args:
            image: Input image as numpy array
            use_ocr: Whether to use OCR for cell text extraction
            
        Returns:
            List of extracted TableStructure objects
        """
        # Detect table regions
        table_bboxes = self.detector.detect_tables(image)
        
        tables = []
        for bbox in table_bboxes:
            x, y, w, h = bbox
            table_region = image[y:y+h, x:x+w]
            
            # Extract table structure
            table_structure = self._extract_table_structure(table_region, bbox, use_ocr)
            if table_structure:
                tables.append(table_structure)
        
        return tables
    
    def _extract_table_structure(self, table_image: np.ndarray, 
                                 bbox: Tuple[int, int, int, int],
                                 use_ocr: bool) -> Optional[TableStructure]:
        """
        Extract structure from a single table region
        
        Args:
            table_image: Cropped table region
            bbox: Bounding box of table in original image
            use_ocr: Whether to use OCR
            
        Returns:
            TableStructure or None if extraction fails
        """
        # Detect cells using grid detection
        cells = self._detect_cells(table_image)
        
        if not cells:
            return None
        
        # Extract text from cells if OCR is enabled
        if use_ocr:
            from .ocr_engine import OCREngine
            ocr = OCREngine()
            
            for cell in cells:
                cx, cy, cw, ch = cell.bbox
                cell_image = table_image[cy:cy+ch, cx:cx+cw]
                result = ocr.extract_text(cell_image)
                cell.text = result.text.strip()
     
   
        # Organize cells into rows and columns
        rows_data = self._organize_cells_into_rows(cells)
        
        # Extract headers (first row)
        headers = rows_data[0] if rows_data else []
        
        # Extract data rows
        data_rows = rows_data[1:] if len(rows_data) > 1 else []
        
        # Detect nested columns
        nested_cols = self._detect_nested_columns(cells)
        
        return TableStructure(
            headers=headers,
            rows=data_rows,
            cells=cells,
            bbox=bbox,
            nested_columns=nested_cols
        )
    
    def _detect_cells(self, table_image: np.ndarray) -> List[TableCell]:
        """
        Detect individual cells in table
        
        Args:
            table_image: Table region image
            
        Returns:
            List of TableCell objects
        """
        # Convert to grayscale
        if len(table_image.shape) == 3:
            gray = cv2.cvtColor(table_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = table_image
        
        # Apply binary threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Invert to get cell regions
        inverted = cv2.bitwise_not(binary)
        
        # Find contours for cells
        contours, _ = cv2.findContours(inverted, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        cells = []
        for idx, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter small contours
            if w > 20 and h > 10:
                cell = TableCell(
                    row=-1,  # Will be assigned later
                    col=-1,  # Will be assigned later
                    text="",
                    bbox=(x, y, w, h)
                )
                cells.append(cell)
        
        return cells
    
  
  def _organize_cells_into_rows(self, cells: List[TableCell]) -> List[List[str]]:
        """
        Organize cells into rows based on vertical position
        
        Args:
            cells: List of TableCell objects
            
        Returns:
            List of rows, each containing cell texts
        """
        if not cells:
            return []
        
        # Sort cells by vertical position (y coordinate)
        sorted_cells = sorted(cells, key=lambda c: c.bbox[1])
        
        # Group cells into rows based on y-coordinate proximity
        rows = []
        current_row = []
        current_y = sorted_cells[0].bbox[1]
        y_threshold = 10  # Pixels tolerance for same row
        
        for cell in sorted_cells:
            cell_y = cell.bbox[1]
            
            if abs(cell_y - current_y) <= y_threshold:
                current_row.append(cell)
            else:
                # Sort current row by x coordinate
                current_row.sort(key=lambda c: c.bbox[0])
                rows.append([c.text for c in current_row])
                
                current_row = [cell]
                current_y = cell_y
        
        # Add last row
        if current_row:
            current_row.sort(key=lambda c: c.bbox[0])
            rows.append([c.text for c in current_row])
        
        return rows
    
    def _detect_nested_columns(self, cells: List[TableCell]) -> Optional[Dict[str, List[str]]]:
        """
        Detect nested column structures
        
        Args:
            cells: List of TableCell objects
            
        Returns:
            Dictionary mapping parent columns to child columns, or None
        """
        # Simplified implementation - can be enhanced
        # For now, return None (no nested columns detected)
        return None


class MultiPageTableHandler:
    """
    Handles tables that span multiple pages
    """
    
   
 def __init__(self):
        """Initialize multi-page table handler"""
        self.extractor = TableExtractor()
    
    def combine_multipage_tables(self, tables: List[TableStructure]) -> List[TableStructure]:
        """
        Combine tables that span multiple pages
        
        Args:
            tables: List of tables from multiple pages
            
        Returns:
            List of combined tables
        """
        if len(tables) <= 1:
            return tables
        
        combined = []
        current_table = None
        
        for table in tables:
            if current_table is None:
                current_table = table
            else:
                # Check if this table continues from previous page
                if self._is_continuation(current_table, table):
                    current_table = self._merge_tables(current_table, table)
                else:
                    combined.append(current_table)
                    current_table = table
        
        if current_table:
            combined.append(current_table)
        
        return combined
    
    def _is_continuation(self, table1: TableStructure, table2: TableStructure) -> bool:
        """
        Check if table2 is a continuation of table1
        
        Args:
            table1: First table
            table2: Second table
            
        Returns:
            True if table2 continues table1
        """
        # Check if headers match
        if len(table1.headers) != len(table2.headers):
            return False
        
        # Simple heuristic: if headers are similar, it's likely a continuation
        return True
    
    def _merge_tables(self, table1: TableStructure, table2: TableStructure) -> TableStructure:
        """
        Merge two tables into one
        
        Args:
            table1: First table
            table2: Second table (continuation)
            
        Returns:
            Merged TableStructure
        """
        merged_rows = table1.rows + table2.rows
        merged_cells = table1.cells + table2.cells
        
        return TableStructure(
            headers=table1.headers,
            rows=merged_rows,
            cells=merged_cells,
            bbox=table1.bbox,
            nested_columns=table1.nested_columns,
            page_number=table1.page_number
        )
