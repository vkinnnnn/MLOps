"""
Document preprocessing module for preparing documents for OCR.
"""
import os
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import cv2
from pdf2image import convert_from_path
import PyPDF2


class ProcessedDocument:
    """Container for processed document data."""
    
    def __init__(
        self, 
        document_id: str, 
        pages: List[np.ndarray],
        original_format: str
    ):
        """
        Initialize processed document.
        
        Args:
            document_id: Unique identifier for the document
            pages: List of page images as numpy arrays
            original_format: Original file format (pdf, jpeg, png, tiff)
        """
        self.document_id = document_id
        self.pages = pages
        self.original_format = original_format
        self.page_count = len(pages)


class DocumentPreprocessor:
    """Handles document preprocessing for OCR optimization."""
    
    def __init__(self, output_dir: str = "processed"):
        """
        Initialize the document preprocessor.
        
        Args:
            output_dir: Directory to store processed documents
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def preprocess_document(
        self, 
        file_path: str, 
        file_type: str,
        document_id: str
    ) -> ProcessedDocument:
        """
        Preprocess a document for OCR.
        
        Args:
            file_path: Path to the document file
            file_type: Type of file (pdf, jpeg, png, tiff)
            document_id: Unique identifier for the document
            
        Returns:
            ProcessedDocument with preprocessed pages
        """
        # Convert document to images
        if file_type == 'pdf':
            pages = self._convert_pdf_to_images(file_path)
        else:
            pages = self._load_image_pages(file_path)
        
        # Preprocess each page
        processed_pages = []
        for page_num, page_image in enumerate(pages):
            processed_page = self._preprocess_image(page_image)
            processed_pages.append(processed_page)
        
        return ProcessedDocument(
            document_id=document_id,
            pages=processed_pages,
            original_format=file_type
        )
    
    def _convert_pdf_to_images(self, pdf_path: str, dpi: int = 300) -> List[np.ndarray]:
        """
        Convert PDF pages to images.
        
        Args:
            pdf_path: Path to the PDF file
            dpi: Resolution for conversion (default: 300)
            
        Returns:
            List of page images as numpy arrays
        """
        try:
            # Convert PDF to PIL images
            pil_images = convert_from_path(pdf_path, dpi=dpi)
            
            # Convert PIL images to numpy arrays
            numpy_images = [np.array(img) for img in pil_images]
            
            return numpy_images
            
        except Exception as e:
            raise ValueError(f"Error converting PDF to images: {str(e)}")
    
    def _load_image_pages(self, image_path: str) -> List[np.ndarray]:
        """
        Load image file(s) - handles multi-page TIFF.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of page images as numpy arrays
        """
        try:
            pages = []
            
            with Image.open(image_path) as img:
                # Check if multi-page (TIFF)
                if hasattr(img, 'n_frames'):
                    for i in range(img.n_frames):
                        img.seek(i)
                        page_array = np.array(img.convert('RGB'))
                        pages.append(page_array)
                else:
                    # Single page image
                    page_array = np.array(img.convert('RGB'))
                    pages.append(page_array)
            
            return pages
            
        except Exception as e:
            raise ValueError(f"Error loading image: {str(e)}")
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Apply preprocessing to improve OCR accuracy.
        
        Preprocessing steps:
        1. Resize if too large or too small
        2. Convert to grayscale
        3. Denoise
        4. Adjust contrast
        5. Binarization (optional, based on image quality)
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Preprocessed image as numpy array
        """
        # Step 1: Resize if needed
        image = self._resize_image(image)
        
        # Step 2: Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Step 3: Denoise
        denoised = self._denoise_image(gray)
        
        # Step 4: Adjust contrast
        contrast_adjusted = self._adjust_contrast(denoised)
        
        # Step 5: Adaptive thresholding for better text recognition
        processed = self._apply_adaptive_threshold(contrast_adjusted)
        
        return processed
    
    def _resize_image(
        self, 
        image: np.ndarray, 
        target_width: int = 2000,
        min_width: int = 800
    ) -> np.ndarray:
        """
        Resize image to optimal dimensions for OCR.
        
        Args:
            image: Input image
            target_width: Target width for large images
            min_width: Minimum width for small images
            
        Returns:
            Resized image
        """
        height, width = image.shape[:2]
        
        # If image is too large, scale down
        if width > target_width:
            scale = target_width / width
            new_width = target_width
            new_height = int(height * scale)
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            return resized
        
        # If image is too small, scale up
        elif width < min_width:
            scale = min_width / width
            new_width = min_width
            new_height = int(height * scale)
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            return resized
        
        return image

    
def _denoise_image(self, image: np.ndarray) -> np.ndarray:
        """
        Remove noise from the image.
        
        Args:
            image: Input grayscale image
            
        Returns:
            Denoised image
        """
        # Use Non-local Means Denoising for better quality
        denoised = cv2.fastNlMeansDenoising(image, None, h=10, templateWindowSize=7, searchWindowSize=21)
        return denoised
    
    def _adjust_contrast(self, image: np.ndarray, clip_limit: float = 2.0) -> np.ndarray:
        """
        Adjust image contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization).
        
        Args:
            image: Input grayscale image
            clip_limit: Threshold for contrast limiting
            
        Returns:
            Contrast-adjusted image
        """
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
        contrast_adjusted = clahe.apply(image)
        return contrast_adjusted
    
    def _apply_adaptive_threshold(self, image: np.ndarray) -> np.ndarray:
        """
        Apply adaptive thresholding for better text extraction.
        
        Args:
            image: Input grayscale image
            
        Returns:
            Binarized image
        """
        # Use adaptive thresholding to handle varying lighting conditions
        binary = cv2.adaptiveThreshold(
            image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        return binary
    
    def save_processed_pages(
        self, 
        processed_doc: ProcessedDocument,
        output_format: str = 'png'
    ) -> List[str]:
        """
        Save processed pages to disk.
        
        Args:
            processed_doc: ProcessedDocument object
            output_format: Output image format (default: png)
            
        Returns:
            List of file paths for saved pages
        """
        saved_paths = []
        
        for page_num, page_image in enumerate(processed_doc.pages):
            # Create filename
            filename = f"{processed_doc.document_id}_page_{page_num + 1}.{output_format}"
            filepath = self.output_dir / filename
            
            # Convert numpy array to PIL Image and save
            if len(page_image.shape) == 2:
                # Grayscale
                pil_image = Image.fromarray(page_image, mode='L')
            else:
                # RGB
                pil_image = Image.fromarray(page_image, mode='RGB')
            
            pil_image.save(filepath)
            saved_paths.append(str(filepath))
        
        return saved_paths
    
    def get_page_as_bytes(self, page_image: np.ndarray, format: str = 'PNG') -> bytes:
        """
        Convert a page image to bytes.
        
        Args:
            page_image: Page image as numpy array
            format: Output format (PNG, JPEG, etc.)
            
        Returns:
            Image as bytes
        """
        from io import BytesIO
        
        if len(page_image.shape) == 2:
            pil_image = Image.fromarray(page_image, mode='L')
        else:
            pil_image = Image.fromarray(page_image, mode='RGB')
        
        buffer = BytesIO()
        pil_image.save(buffer, format=format)
        return buffer.getvalue()
