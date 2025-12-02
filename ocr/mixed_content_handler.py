"""
Mixed Content Handler Module

Extracts and preserves numbers, special characters, currency symbols,
and maintains context for mixed text-number content.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ContentType(Enum):
    """Types of content elements"""
    TEXT = "text"
    NUMBER = "number"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    DATE = "date"
    SPECIAL_CHAR = "special_char"


@dataclass
class ContentElement:
    """Represents a single content element"""
    content_type: ContentType
    value: str
    original_text: str
    position: int


@dataclass
class MixedContent:
    """Container for mixed content extraction results"""
    original_text: str
    elements: List[ContentElement]
    structured_data: Dict[str, any]


class MixedContentHandler:
    """
    Handles extraction and preservation of mixed content including
    text, numbers, currency symbols, and special characters.
    """
    
    def __init__(self):
        """Initialize mixed content handler"""
        # Currency symbols
        self.currency_symbols = ['$', '€', '£', '¥', '₹', '₨', 'Rs', 'INR', 'USD', 'EUR']
        
        # Patterns for different content types
        self.patterns = {
            'currency': r'(?:Rs\.?|INR|USD|EUR|₹|\$|€|£|¥)\s*[\d,]+(?:\.\d{2})?',
            'percentage': r'\d+(?:\.\d+)?%',
            'number': r'\d+(?:,\d{3})*(?:\.\d+)?',
            'date': r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        }
    
 
   def extract_mixed_content(self, text: str) -> MixedContent:
        """
        Extract and classify mixed content from text
        
        Args:
            text: Input text containing mixed content
            
        Returns:
            MixedContent object with classified elements
        """
        elements = []
        
        # Extract currency values
        for match in re.finditer(self.patterns['currency'], text):
            element = ContentElement(
                content_type=ContentType.CURRENCY,
                value=self._normalize_currency(match.group()),
                original_text=match.group(),
                position=match.start()
            )
            elements.append(element)
        
        # Extract percentages
        for match in re.finditer(self.patterns['percentage'], text):
            element = ContentElement(
                content_type=ContentType.PERCENTAGE,
                value=self._normalize_percentage(match.group()),
                original_text=match.group(),
                position=match.start()
            )
            elements.append(element)
        
        # Extract dates
        for match in re.finditer(self.patterns['date'], text):
            element = ContentElement(
                content_type=ContentType.DATE,
                value=match.group(),
                original_text=match.group(),
                position=match.start()
            )
            elements.append(element)
        
        # Extract standalone numbers (not part of currency or percentage)
        for match in re.finditer(self.patterns['number'], text):
            # Check if this number is not part of currency or percentage
            if not self._is_part_of_other_element(match.start(), elements):
                element = ContentElement(
                    content_type=ContentType.NUMBER,
                    value=self._normalize_number(match.group()),
                    original_text=match.group(),
                    position=match.start()
                )
                elements.append(element)
        
        # Sort elements by position
        elements.sort(key=lambda e: e.position)
        
        # Create structured data
        structured_data = self._create_structured_data(elements)
        
        return MixedContent(
            original_text=text,
            elements=elements,
            structured_data=structured_data
        )
    
    
def extract_numbers(self, text: str) -> List[float]:
        """
        Extract all numbers from text
        
        Args:
            text: Input text
            
        Returns:
            List of extracted numbers as floats
        """
        numbers = []
        for match in re.finditer(self.patterns['number'], text):
            try:
                num_str = match.group().replace(',', '')
                numbers.append(float(num_str))
            except ValueError:
                continue
        return numbers
    
    def extract_currency_values(self, text: str) -> List[Tuple[str, float]]:
        """
        Extract currency values with their symbols
        
        Args:
            text: Input text
            
        Returns:
            List of (currency_symbol, amount) tuples
        """
        currency_values = []
        for match in re.finditer(self.patterns['currency'], text):
            currency_str = match.group()
            symbol, amount = self._parse_currency(currency_str)
            currency_values.append((symbol, amount))
        return currency_values
    
    def extract_special_characters(self, text: str) -> List[str]:
        """
        Extract special characters from text
        
        Args:
            text: Input text
            
        Returns:
            List of special characters found
        """
        # Define special characters to extract
        special_chars = set()
        for char in text:
            if not char.isalnum() and not char.isspace():
                special_chars.add(char)
        return list(special_chars)
    
    def preserve_context(self, text: str, window_size: int = 50) -> Dict[str, List[str]]:
        """
        Preserve context around important elements (numbers, currency)
        
        Args:
            text: Input text
            window_size: Number of characters to include before/after element
            
        Returns:
            Dictionary mapping element to its context
        """
        mixed_content = self.extract_mixed_content(text)
        context_map = {}
        
        for element in mixed_content.elements:
            if element.content_type in [ContentType.CURRENCY, ContentType.NUMBER, ContentType.PERCENTAGE]:
                start = max(0, element.position - window_size)
                end = min(len(text), element.position + len(element.original_text) + window_size)
                context = text[start:end]
                
                key = f"{element.content_type.value}:{element.value}"
                if key not in context_map:
                    context_map[key] = []
                context_map[key].append(context)
        
        return context_map
 
   
    def _normalize_currency(self, currency_str: str) -> str:
        """Normalize currency string to standard format"""
        # Remove spaces and standardize
        currency_str = currency_str.strip()
        # Extract numeric value
        numeric_part = re.search(r'[\d,]+(?:\.\d{2})?', currency_str)
        if numeric_part:
            return numeric_part.group().replace(',', '')
        return currency_str
    
    def _normalize_percentage(self, percentage_str: str) -> str:
        """Normalize percentage string"""
        return percentage_str.replace('%', '').strip()
    
    def _normalize_number(self, number_str: str) -> str:
        """Normalize number string"""
        return number_str.replace(',', '').strip()
    
    def _parse_currency(self, currency_str: str) -> Tuple[str, float]:
        """
        Parse currency string into symbol and amount
        
        Args:
            currency_str: Currency string like "Rs. 50,000" or "$1,234.56"
            
        Returns:
            Tuple of (symbol, amount)
        """
        # Extract symbol
        symbol = "INR"  # Default
        for sym in self.currency_symbols:
            if sym in currency_str:
                symbol = sym
                break
        
        # Extract amount
        numeric_part = re.search(r'[\d,]+(?:\.\d{2})?', currency_str)
        amount = 0.0
        if numeric_part:
            try:
                amount = float(numeric_part.group().replace(',', ''))
            except ValueError:
                pass
        
        return (symbol, amount)
    
    def _is_part_of_other_element(self, position: int, elements: List[ContentElement]) -> bool:
        """Check if position is part of an already extracted element"""
        for element in elements:
            if element.position <= position < element.position + len(element.original_text):
                return True
        return False
    
    def _create_structured_data(self, elements: List[ContentElement]) -> Dict[str, any]:
        """Create structured data from elements"""
        structured = {
            'currencies': [],
            'percentages': [],
            'numbers': [],
            'dates': []
        }
        
        for element in elements:
            if element.content_type == ContentType.CURRENCY:
                structured['currencies'].append(element.value)
            elif element.content_type == ContentType.PERCENTAGE:
                structured['percentages'].append(element.value)
            elif element.content_type == ContentType.NUMBER:
                structured['numbers'].append(element.value)
            elif element.content_type == ContentType.DATE:
                structured['dates'].append(element.value)
        
        return structured
