"""
Field extractor for extracting core loan terms from OCR text.
Handles extraction of principal amount, interest rate, tenure, and moratorium period.
"""

import re
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal


class CoreLoanFieldExtractor:
    """Extracts core loan terms using pattern matching and NER."""
    
    def __init__(self):
        # Patterns for principal amount
        self.principal_patterns = [
            r'(?:principal|loan\s+amount|amount\s+sanctioned|disbursement\s+amount)[:\s]*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'(?:rs\.?|inr|₹)\s*([0-9,]+(?:\.[0-9]{2})?)\s*(?:principal|loan\s+amount)',
            r'amount\s+of\s+loan[:\s]*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)',
        ]
        
        # Patterns for interest rate
        self.interest_patterns = [
            r'(?:interest\s+rate|rate\s+of\s+interest|roi)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*%?\s*(?:p\.?a\.?|per\s+annum)?',
            r'([0-9]+(?:\.[0-9]+)?)\s*%\s*(?:p\.?a\.?|per\s+annum)?\s*(?:interest|roi)',
            r'apr[:\s]*([0-9]+(?:\.[0-9]+)?)\s*%?',
        ]
        
        # Patterns for tenure
        self.tenure_patterns = [
            r'(?:tenure|loan\s+period|repayment\s+period|term)[:\s]*([0-9]+)\s*(months?|years?)',
            r'(?:period\s+of|duration\s+of)\s+(?:loan|repayment)[:\s]*([0-9]+)\s*(months?|years?)',
            r'([0-9]+)\s*(months?|years?)\s*(?:tenure|period|term)',
        ]
        
        # Patterns for moratorium period
        self.moratorium_patterns = [
            r'(?:moratorium|grace\s+period)[:\s]*([0-9]+)\s*(months?|years?)',
            r'(?:repayment\s+starts\s+after|payment\s+holiday)[:\s]*([0-9]+)\s*(months?|years?)',
            r'([0-9]+)\s*(months?|years?)\s*(?:moratorium|grace\s+period)',
        ]
    
    def extract_principal_amount(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract principal amount from text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with amount and confidence score, or None
        """
        text_lower = text.lower()
        
        for pattern in self.principal_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1).replace(',', '')
                try:
                    amount = float(amount_str)
                    # Validate reasonable loan amount (100 to 100 crores)
                    if 100 <= amount <= 1000000000:
                        return {
                            'value': amount,
                            'currency': 'INR',
                            'confidence': 0.9,
                            'source_text': match.group(0)
                        }
                except ValueError:
                    continue
        
        return None
    
    def extract_interest_rate(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract interest rate or APR from text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with rate and confidence score, or None
        """
        text_lower = text.lower()
        
        for pattern in self.interest_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                rate_str = match.group(1)
                try:
                    rate = float(rate_str)
                    # Validate reasonable interest rate (0.1% to 50%)
                    if 0.1 <= rate <= 50:
                        return {
                            'value': rate,
                            'unit': 'percent_per_annum',
                            'confidence': 0.9,
                            'source_text': match.group(0)
                        }
                except ValueError:
                    continue
        
        return None
    
    def extract_tenure(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract loan tenure in months or years.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with tenure in months and confidence score, or None
        """
        text_lower = text.lower()
        
        for pattern in self.tenure_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                duration_str = match.group(1)
                unit = match.group(2).lower()
                
                try:
                    duration = int(duration_str)
                    
                    # Convert to months
                    if 'year' in unit:
                        tenure_months = duration * 12
                    else:
                        tenure_months = duration
                    
                    # Validate reasonable tenure (1 month to 30 years)
                    if 1 <= tenure_months <= 360:
                        return {
                            'value': tenure_months,
                            'unit': 'months',
                            'original_value': duration,
                            'original_unit': unit,
                            'confidence': 0.9,
                            'source_text': match.group(0)
                        }
                except ValueError:
                    continue
        
        return None
    
    def extract_moratorium_period(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract moratorium/grace period.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with moratorium period in months and confidence score, or None
        """
        text_lower = text.lower()
        
        for pattern in self.moratorium_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                duration_str = match.group(1)
                unit = match.group(2).lower()
                
                try:
                    duration = int(duration_str)
                    
                    # Convert to months
                    if 'year' in unit:
                        moratorium_months = duration * 12
                    else:
                        moratorium_months = duration
                    
                    # Validate reasonable moratorium (0 to 5 years)
                    if 0 <= moratorium_months <= 60:
                        return {
                            'value': moratorium_months,
                            'unit': 'months',
                            'original_value': duration,
                            'original_unit': unit,
                            'confidence': 0.85,
                            'source_text': match.group(0)
                        }
                except ValueError:
                    continue
        
        return None
    
    def extract_all_core_fields(self, text: str) -> Dict[str, Any]:
        """
        Extract all core loan fields from text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary containing all extracted core fields
        """
        return {
            'principal_amount': self.extract_principal_amount(text),
            'interest_rate': self.extract_interest_rate(text),
            'tenure': self.extract_tenure(text),
            'moratorium_period': self.extract_moratorium_period(text)
        }
