"""
Fee and penalty extractor for loan documents.
Handles extraction of processing fees, administrative fees, documentation charges, and penalty clauses.
"""

import re
from typing import Optional, Dict, Any, List


class FeeAndPenaltyExtractor:
    """Extracts fees and penalty information from loan documents."""
    
    def __init__(self):
        # Patterns for various fees
        self.processing_fee_patterns = [
            r'(?:processing\s+fee|processing\s+charges?)[:\s]*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'(?:processing\s+fee|processing\s+charges?)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*%',
        ]
        
        self.admin_fee_patterns = [
            r'(?:administrative\s+fee|admin\s+fee|administration\s+charges?)[:\s]*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'(?:administrative\s+fee|admin\s+fee)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*%',
        ]
        
        self.documentation_fee_patterns = [
            r'(?:documentation\s+fee|documentation\s+charges?|document\s+charges?)[:\s]*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)',
        ]
        
        # Patterns for penalties
        self.late_payment_patterns = [
            r'(?:late\s+payment|delayed\s+payment|overdue)\s+(?:penalty|charges?|fee)[:\s]*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'(?:late\s+payment|delayed\s+payment|overdue)\s+(?:penalty|charges?|fee)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*%',
            r'(?:penalty|charges?)\s+(?:for|on)\s+(?:late|delayed|overdue)\s+payment[:\s]*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)',
        ]
        
        self.prepayment_penalty_patterns = [
            r'(?:prepayment|pre-payment|foreclosure)\s+(?:penalty|charges?|fee)[:\s]*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'(?:prepayment|pre-payment|foreclosure)\s+(?:penalty|charges?|fee)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*%',
            r'(?:penalty|charges?)\s+(?:for|on)\s+(?:prepayment|pre-payment|foreclosure)[:\s]*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)',
        ]
    
    def extract_processing_fee(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract processing fee from text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with fee details and confidence score, or None
        """
        text_lower = text.lower()
        
        for pattern in self.processing_fee_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                fee_str = match.group(1).replace(',', '')
                
                # Check if it's a percentage or fixed amount
                if '%' in match.group(0):
                    try:
                        percentage = float(fee_str)
                        if 0 <= percentage <= 10:  # Reasonable processing fee percentage
                            return {
                                'type': 'processing_fee',
                                'value': percentage,
                                'value_type': 'percentage',
                                'confidence': 0.85,
                                'source_text': match.group(0)
                            }
                    except ValueError:
                        continue
                else:
                    try:
                        amount = float(fee_str)
                        if 0 <= amount <= 1000000:  # Reasonable processing fee amount
                            return {
                                'type': 'processing_fee',
                                'value': amount,
                                'value_type': 'fixed',
                                'currency': 'INR',
                                'confidence': 0.85,
                                'source_text': match.group(0)
                            }
                    except ValueError:
                        continue
        
        return None
    
    def extract_administrative_fee(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract administrative fee from text."""
        text_lower = text.lower()
        
        for pattern in self.admin_fee_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                fee_str = match.group(1).replace(',', '')
                
                if '%' in match.group(0):
                    try:
                        percentage = float(fee_str)
                        if 0 <= percentage <= 5:
                            return {
                                'type': 'administrative_fee',
                                'value': percentage,
                                'value_type': 'percentage',
                                'confidence': 0.85,
                                'source_text': match.group(0)
                            }
                    except ValueError:
                        continue
                else:
                    try:
                        amount = float(fee_str)
                        if 0 <= amount <= 500000:
                            return {
                                'type': 'administrative_fee',
                                'value': amount,
                                'value_type': 'fixed',
                                'currency': 'INR',
                                'confidence': 0.85,
                                'source_text': match.group(0)
                            }
                    except ValueError:
                        continue
        
        return None
    
    def extract_documentation_fee(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract documentation charges from text."""
        text_lower = text.lower()
        
        for pattern in self.documentation_fee_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                fee_str = match.group(1).replace(',', '')
                
                try:
                    amount = float(fee_str)
                    if 0 <= amount <= 100000:
                        return {
                            'type': 'documentation_fee',
                            'value': amount,
                            'value_type': 'fixed',
                            'currency': 'INR',
                            'confidence': 0.85,
                            'source_text': match.group(0)
                        }
                except ValueError:
                    continue
        
        return None
    
    def extract_late_payment_penalty(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract late payment penalty clause from text."""
        text_lower = text.lower()
        
        for pattern in self.late_payment_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                penalty_str = match.group(1).replace(',', '')
                
                if '%' in match.group(0):
                    try:
                        percentage = float(penalty_str)
                        if 0 <= percentage <= 10:
                            return {
                                'type': 'late_payment_penalty',
                                'value': percentage,
                                'value_type': 'percentage',
                                'confidence': 0.8,
                                'source_text': match.group(0)
                            }
                    except ValueError:
                        continue
                else:
                    try:
                        amount = float(penalty_str)
                        if 0 <= amount <= 100000:
                            return {
                                'type': 'late_payment_penalty',
                                'value': amount,
                                'value_type': 'fixed',
                                'currency': 'INR',
                                'confidence': 0.8,
                                'source_text': match.group(0)
                            }
                    except ValueError:
                        continue
        
        return None
    
    def extract_prepayment_penalty(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract prepayment penalty clause from text."""
        text_lower = text.lower()
        
        for pattern in self.prepayment_penalty_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                penalty_str = match.group(1).replace(',', '')
                
                if '%' in match.group(0):
                    try:
                        percentage = float(penalty_str)
                        if 0 <= percentage <= 10:
                            return {
                                'type': 'prepayment_penalty',
                                'value': percentage,
                                'value_type': 'percentage',
                                'confidence': 0.8,
                                'source_text': match.group(0)
                            }
                    except ValueError:
                        continue
                else:
                    try:
                        amount = float(penalty_str)
                        if 0 <= amount <= 500000:
                            return {
                                'type': 'prepayment_penalty',
                                'value': amount,
                                'value_type': 'fixed',
                                'currency': 'INR',
                                'confidence': 0.8,
                                'source_text': match.group(0)
                            }
                    except ValueError:
                        continue
        
        return None
    
    def extract_fees_from_table(self, table_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract fee structures from table data.
        
        Args:
            table_data: Structured table data with headers and rows
            
        Returns:
            List of extracted fee items
        """
        fees = []
        
        if not table_data or 'headers' not in table_data or 'rows' not in table_data:
            return fees
        
        headers = [h.lower() for h in table_data['headers']]
        
        # Find relevant columns
        fee_type_col = None
        amount_col = None
        
        for i, header in enumerate(headers):
            if any(term in header for term in ['fee', 'charge', 'cost', 'expense']):
                if 'type' in header or 'description' in header or 'particular' in header:
                    fee_type_col = i
                elif 'amount' in header or 'value' in header or 'rs' in header:
                    amount_col = i
        
        # Extract fees from rows
        if fee_type_col is not None and amount_col is not None:
            for row in table_data['rows']:
                if len(row) > max(fee_type_col, amount_col):
                    fee_type = row[fee_type_col].strip()
                    amount_str = row[amount_col].strip().replace(',', '').replace('₹', '').replace('Rs.', '')
                    
                    try:
                        amount = float(re.sub(r'[^\d.]', '', amount_str))
                        fees.append({
                            'type': fee_type,
                            'value': amount,
                            'value_type': 'fixed',
                            'currency': 'INR',
                            'confidence': 0.9,
                            'source': 'table'
                        })
                    except (ValueError, AttributeError):
                        continue
        
        return fees
    
    def extract_all_fees_and_penalties(self, text: str, tables: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extract all fees and penalties from text and tables.
        
        Args:
            text: OCR extracted text
            tables: List of extracted table data
            
        Returns:
            Dictionary containing all extracted fees and penalties
        """
        result = {
            'fees': [],
            'penalties': []
        }
        
        # Extract from text
        processing_fee = self.extract_processing_fee(text)
        if processing_fee:
            result['fees'].append(processing_fee)
        
        admin_fee = self.extract_administrative_fee(text)
        if admin_fee:
            result['fees'].append(admin_fee)
        
        doc_fee = self.extract_documentation_fee(text)
        if doc_fee:
            result['fees'].append(doc_fee)
        
        late_penalty = self.extract_late_payment_penalty(text)
        if late_penalty:
            result['penalties'].append(late_penalty)
        
        prepay_penalty = self.extract_prepayment_penalty(text)
        if prepay_penalty:
            result['penalties'].append(prepay_penalty)
        
        # Extract from tables
        if tables:
            for table in tables:
                table_fees = self.extract_fees_from_table(table)
                result['fees'].extend(table_fees)
        
        return result
