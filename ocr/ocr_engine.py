"""
OCR Engine Wrapper Module

Provides OCR functionality using Tesseract for printed text
and confidence scoring mechanisms.
"""

import pytesseract
from PIL import Image
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import cv2


@dataclass
class OCRResult:
    """Container for OCR extraction results"""
    text: str
    confidence: float
    word_confidences: List[Tuple[str, float]]
    bounding_boxes: List[Tuple[int, int, int, int]]


class OCREngine:
    """
    OCR Engine wrapper supporting Tesseract for printed text extraction
    with confidence scoring.
    """
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize OCR Engine
        
        Args:
            tesseract_cmd: Path to tesseract executable (optional)
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        self.config = '--oem 3 --psm 6'  # LSTM OCR Engine, assume uniform text block
    
    def extract_text(self, image: np.ndarray) -> OCRResult:
        """
        Extract text from image using Tesseract OCR
        
        Args:
            image: Input image as numpy array
            
        Returns:
            OCRResult containing extracted text and confidence scores
        """
     
   # Convert numpy array to PIL Image if needed
        if isinstance(image, np.ndarray):
            image_pil = Image.fromarray(image)
        else:
            image_pil = image
        
        # Extract text with detailed data
        data = pytesseract.image_to_data(image_pil, config=self.config, output_type=pytesseract.Output.DICT)
        
        # Extract full text
        text = pytesseract.image_to_string(image_pil, config=self.config)
        
        # Calculate word-level confidences and bounding boxes
        word_confidences = []
        bounding_boxes = []
        
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            if int(data['conf'][i]) > 0:  # Filter out empty detections
                word = data['text'][i].strip()
                if word:
                    conf = float(data['conf'][i]) / 100.0  # Normalize to 0-1
                    word_confidences.append((word, conf))
                    
                    # Bounding box (x, y, width, height)
                    bbox = (
                        data['left'][i],
                        data['top'][i],
                        data['width'][i],
                        data['height'][i]
                    )
                    bounding_boxes.append(bbox)
        
        # Calculate overall confidence
        overall_confidence = self._calculate_confidence(word_confidences)
        
        return OCRResult(
            text=text,
            confidence=overall_confidence,
            word_confidences=word_confidences,
            bounding_boxes=bounding_boxes
        )
    
    def extract_text_from_region(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> OCRResult:
        """
        Extract text from specific region of image
        
        Args:
            image: Input image as numpy array
            bbox: Bounding box as (x, y, width, height)
            
        Returns:
            OCRResult for the specified region
        """
 
       x, y, w, h = bbox
        region = image[y:y+h, x:x+w]
        return self.extract_text(region)
    
    def _calculate_confidence(self, word_confidences: List[Tuple[str, float]]) -> float:
        """
        Calculate overall confidence score from word-level confidences
        
        Args:
            word_confidences: List of (word, confidence) tuples
            
        Returns:
            Overall confidence score (0.0 to 1.0)
        """
        if not word_confidences:
            return 0.0
        
        # Weighted average based on word length
        total_weight = 0
        weighted_sum = 0
        
        for word, conf in word_confidences:
            weight = len(word)
            weighted_sum += conf * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image to improve OCR accuracy
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply adaptive thresholding for better contrast
        binary = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return binary


class HandwritingRecognizer:
    """
    Placeholder for handwriting recognition using Donut or LayoutLMv3
    """
    

    def __init__(self):
        """Initialize handwriting recognizer"""
        # Placeholder for future implementation with Donut/LayoutLMv3
        self.model = None
    
    def extract_handwritten_text(self, image: np.ndarray) -> OCRResult:
        """
        Extract handwritten text from image
        
        Args:
            image: Input image as numpy array
            
        Returns:
            OCRResult containing extracted handwritten text
        """
        # Placeholder implementation - falls back to Tesseract for now
        # In production, this would use Donut or LayoutLMv3
        ocr_engine = OCREngine()
        return ocr_engine.extract_text(image)
