# OCR Module

This module provides comprehensive OCR and document analysis capabilities for the Student Loan Document Extractor Platform.

## Features

- **Text Extraction**: Tesseract OCR integration for printed text with confidence scoring
- **Layout Analysis**: Document structure detection (headers, text blocks, tables)
- **Table Extraction**: Automatic table detection and data extraction
- **Mixed Content Handling**: Extract and preserve numbers, currency, percentages, special characters
- **Multi-page Processing**: Sequential page processing with context maintenance

## Components

### OCREngine
Wrapper for Tesseract OCR with preprocessing and confidence scoring.

```python
from ocr import OCREngine
import cv2

# Initialize OCR engine
ocr = OCREngine()

# Load image
image = cv2.imread('document.jpg')

# Extract text
result = ocr.extract_text(image)
print(f"Text: {result.text}")
print(f"Confidence: {result.confidence}")
```

### LayoutAnalyzer
Analyzes document structure and identifies regions.

```python
from ocr import LayoutAnalyzer

analyzer = LayoutAnalyzer()
layout = analyzer.analyze_layout(image)

print(f"Found {len(layout.text_blocks)} text blocks")
print(f"Found {len(layout.tables)} tables")
print(f"Found {len(layout.headers)} headers")
```

### TableExtractor
Detects and extracts table structures.

```python
from ocr import TableExtractor

extractor = TableExtractor()
tables = extractor.extract_tables(image, use_ocr=True)

for table in tables:
 print(f"Headers: {table.headers}")
 print(f"Rows: {len(table.rows)}")
```

### MixedContentHandler
Extracts numbers, currency, percentages, and special characters.

```python
from ocr import MixedContentHandler

handler = MixedContentHandler()
mixed = handler.extract_mixed_content(text)

print(f"Currencies: {mixed.structured_data['currencies']}")
print(f"Percentages: {mixed.structured_data['percentages']}")
```

### MultiPageProcessor
Processes multi-page documents with context maintenance.

```python
from ocr import MultiPageProcessor
import cv2

processor = MultiPageProcessor()

# Load pages
pages = [cv2.imread(f'page_{i}.jpg') for i in range(1, 6)]

# Process document
doc_content = processor.process_document(pages)

print(f"Total pages: {doc_content.total_pages}")
print(f"Combined text length: {len(doc_content.combined_text)}")
print(f"Total tables: {len(doc_content.all_tables)}")
```

### OCRService
High-level service integrating all components.

```python
from ocr import OCRService

service = OCRService()

# Process single page
result = service.process_single_page(image)

# Process multi-page document
doc_content = service.process_multipage_document(pages)

# Quick text extraction
text = service.extract_text_only(image)
```

## Requirements

- pytesseract
- opencv-python
- numpy
- Pillow
- Tesseract OCR (system installation required)

## Installation

Install Tesseract OCR on your system:

**Windows:**
```bash
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
# Add to PATH or specify path in OCREngine initialization
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

You can specify the Tesseract executable path:

```python
ocr = OCREngine(tesseract_cmd=r'C:\Program Files\Tesseract-OCR\tesseract.exe')
```

## Performance

- Single page processing: ~2-5 seconds (depending on image size and complexity)
- Multi-page documents: Sequential processing, ~2-5 seconds per page
- Maximum supported pages: 50 pages per document

## Confidence Scoring

OCR results include confidence scores (0.0 to 1.0):
- > 0.9: High confidence
- 0.7 - 0.9: Medium confidence
- < 0.7: Low confidence (may require manual review)
