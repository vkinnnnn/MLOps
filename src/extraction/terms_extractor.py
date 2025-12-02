"""
Additional terms extractor for loan documents.
Handles extraction of disbursement terms and repayment mode options.
"""

import re
from typing import Optional, Dict, Any, List


class AdditionalTermsExtractor:
    """Extracts additional loan terms like disbursement and repayment modes."""
    
    def __init__(self):
        # Patterns for disbursement terms
        self.disbursement_patterns = [
            r'(?:disbursement|disbursal)[:\s]*([A-Za-z\s,]+(?:days|weeks|months|tranches|installments))',
            r'(?:loan\s+will\s+be\s+disbursed|amount\s+will\s+be\s+disbursed)[:\s]*([A-Za-z\s,]+)',
            r'(?:disbursement\s+schedule|disbursal\s+terms)[:\s]*([A-Za-z\s,]+)',
        ]
        
        # Patterns for repayment modes
        self.repayment_mode_patterns = [
            r'(?:repayment\s+mode|payment\s+mode|repayment\s+method)[:\s]*(emi|equated\s+monthly\s+installment|bullet|step-up|step\s+up)',
            r'(?:emi|equated\s+monthly\s+installment)',
            r'(?:bullet\s+payment|lump\s+sum\s+payment)',
            r'(?:step-up|step\s+up)\s+(?:payment|emi)',
        ]
        
        # Patterns for EMI details
        self.emi_patterns = [
            r'(?:emi|monthly\s+installment)[:\s]*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'(?:monthly\s+payment)[:\s]*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)',
        ]
    
    def extract_disbursement_terms(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract disbursement terms from text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with disbursement details and confidence score, or None
        """
        text_lower = text.lower()
        
        for pattern in self.disbursement_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                terms = match.group(1).strip()
                
                # Determine disbursement type
                disbursement_type = 'single'
                if any(term in terms for term in ['tranches', 'installments', 'phases', 'stages']):
                    disbursement_type = 'multiple'
                
                return {
                    'type': disbursement_type,
                    'description': terms,
                    'confidence': 0.75,
                    'source_text': match.group(0)
                }
        
        # Check for common disbursement phrases
        if 'single disbursement' in text_lower or 'one-time disbursement' in text_lower:
            return {
                'type': 'single',
                'description': 'Single disbursement',
                'confidence': 0.8
            }
        
        if 'multiple disbursement' in text_lower or 'tranches' in text_lower:
            return {
                'type': 'multiple',
                'description': 'Multiple disbursements/tranches',
                'confidence': 0.8
            }
        
        return None
    
    def extract_repayment_mode(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract repayment mode from text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with repayment mode details and confidence score, or None
        """
        text_lower = text.lower()
        
        # Check for specific repayment modes
        if 'emi' in text_lower or 'equated monthly installment' in text_lower:
            return {
                'mode': 'EMI',
                'description': 'Equated Monthly Installment',
                'confidence': 0.9
            }
        
        if 'bullet payment' in text_lower or 'lump sum payment' in text_lower:
            return {
                'mode': 'bullet',
                'description': 'Bullet payment (lump sum at end)',
                'confidence': 0.85
            }
        
        if 'step-up' in text_lower or 'step up' in text_lower:
            return {
                'mode': 'step-up',
                'description': 'Step-up payment (increasing installments)',
                'confidence': 0.85
            }
        
        # Try pattern matching
        for pattern in self.repayment_mode_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                mode_text = match.group(0)
                
                if 'emi' in mode_text or 'equated' in mode_text:
                    mode = 'EMI'
                    description = 'Equated Monthly Installment'
                elif 'bullet' in mode_text:
                    mode = 'bullet'
                    description = 'Bullet payment'
                elif 'step' in mode_text:
                    mode = 'step-up'
                    description = 'Step-up payment'
                else:
                    continue
                
                return {
                    'mode': mode,
                    'description': description,
                    'confidence': 0.8,
                    'source_text': match.group(0)
                }
        
        return None
    
    def extract_emi_amount(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract EMI amount from text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with EMI amount and confidence score, or None
        """
        text_lower = text.lower()
        
        for pattern in self.emi_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1).replace(',', '')
                
                try:
                    amount = float(amount_str)
                    # Validate reasonable EMI amount (100 to 10 lakhs)
                    if 100 <= amount <= 1000000:
                        return {
                            'value': amount,
                            'currency': 'INR',
                            'confidence': 0.85,
                            'source_text': match.group(0)
                        }
                except ValueError:
                    continue
        
        return None
    
    def extract_prepayment_options(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract prepayment/foreclosure options from text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with prepayment options and confidence score, or None
        """
        text_lower = text.lower()
        
        # Check if prepayment is allowed
        if 'prepayment allowed' in text_lower or 'foreclosure allowed' in text_lower:
            return {
                'allowed': True,
                'description': 'Prepayment/foreclosure allowed',
                'confidence': 0.85
            }
        
        if 'no prepayment' in text_lower or 'prepayment not allowed' in text_lower:
            return {
                'allowed': False,
                'description': 'Prepayment not allowed',
                'confidence': 0.85
            }
        
        # Check for partial prepayment
        if 'partial prepayment' in text_lower:
            return {
                'allowed': True,
                'type': 'partial',
                'description': 'Partial prepayment allowed',
                'confidence': 0.8
            }
        
        return None
    
    def extract_lock_in_period(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract lock-in period from text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with lock-in period and confidence score, or None
        """
        text_lower = text.lower()
        
        pattern = r'(?:lock-in|lock\s+in)\s+period[:\s]*([0-9]+)\s*(months?|years?)'
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        
        for match in matches:
            duration_str = match.group(1)
            unit = match.group(2).lower()
            
            try:
                duration = int(duration_str)
                
                # Convert to months
                if 'year' in unit:
                    lock_in_months = duration * 12
                else:
                    lock_in_months = duration
                
                return {
                    'value': lock_in_months,
                    'unit': 'months',
                    'original_value': duration,
                    'original_unit': unit,
                    'confidence': 0.8,
                    'source_text': match.group(0)
                }
            except ValueError:
                continue
        
        return None
    
    def extract_all_additional_terms(self, text: str) -> Dict[str, Any]:
        """
        Extract all additional loan terms from text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary containing all extracted additional terms
        """
        return {
            'disbursement_terms': self.extract_disbursement_terms(text),
            'repayment_mode': self.extract_repayment_mode(text),
            'emi_amount': self.extract_emi_amount(text),
            'prepayment_options': self.extract_prepayment_options(text),
            'lock_in_period': self.extract_lock_in_period(text)
        }
