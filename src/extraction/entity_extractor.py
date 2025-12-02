"""
Entity extractor for lender and borrower information.
Handles extraction of bank details, co-signer information, and collateral details.
"""

import re
from typing import Optional, Dict, Any, List


class EntityExtractor:
    """Extracts lender, borrower, and related entity information from loan documents."""
    
    def __init__(self):
        # Common Indian bank names
        self.bank_names = [
            'state bank of india', 'sbi', 'hdfc bank', 'icici bank', 'axis bank',
            'punjab national bank', 'pnb', 'bank of baroda', 'canara bank',
            'union bank', 'bank of india', 'indian bank', 'central bank',
            'idbi bank', 'yes bank', 'kotak mahindra', 'indusind bank',
            'federal bank', 'rbl bank', 'idfc first bank', 'bandhan bank',
            'karur vysya bank', 'south indian bank', 'city union bank'
        ]
        
        # Patterns for bank information
        self.bank_patterns = [
            r'(?:lender|bank|financial\s+institution)[:\s]*([A-Z][A-Za-z\s&]+(?:Bank|Ltd|Limited))',
            r'([A-Z][A-Za-z\s&]+(?:Bank|Ltd|Limited))\s+(?:branch|office)',
        ]
        
        self.branch_patterns = [
            r'(?:branch|office)[:\s]*([A-Z][A-Za-z\s,]+)',
            r'(?:branch\s+name|branch\s+address)[:\s]*([A-Za-z\s,]+)',
        ]
        
        # Patterns for co-signer
        self.cosigner_patterns = [
            r'(?:co-signer|co\s+signer|guarantor)[:\s]*([A-Z][A-Za-z\s\.]+)',
            r'(?:parent|guardian)\s+name[:\s]*([A-Z][A-Za-z\s\.]+)',
        ]
        
        self.relationship_patterns = [
            r'(?:relationship|relation)[:\s]*(father|mother|parent|guardian|spouse|sibling)',
        ]
        
        # Patterns for collateral
        self.collateral_patterns = [
            r'(?:collateral|security|pledge)[:\s]*([A-Za-z\s,]+(?:property|asset|gold|vehicle|land|house))',
            r'(?:secured\s+by|security\s+provided)[:\s]*([A-Za-z\s,]+)',
        ]
    
    def extract_bank_name(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract lender/bank name from text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with bank name and confidence score, or None
        """
        text_lower = text.lower()
        
        # First, try to find known bank names
        for bank_name in self.bank_names:
            if bank_name in text_lower:
                # Find the actual case-preserved version
                pattern = re.compile(re.escape(bank_name), re.IGNORECASE)
                match = pattern.search(text)
                if match:
                    return {
                        'bank_name': match.group(0).title(),
                        'confidence': 0.95,
                        'source_text': match.group(0)
                    }
        
        # Try pattern matching
        for pattern in self.bank_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                bank_name = match.group(1).strip()
                if len(bank_name) > 3:  # Avoid very short matches
                    return {
                        'bank_name': bank_name,
                        'confidence': 0.8,
                        'source_text': match.group(0)
                    }
        
        return None
    
    def extract_branch_details(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract branch name/location from text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with branch details and confidence score, or None
        """
        for pattern in self.branch_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                branch_info = match.group(1).strip()
                if len(branch_info) > 3:
                    return {
                        'branch_name': branch_info,
                        'confidence': 0.75,
                        'source_text': match.group(0)
                    }
        
        return None
    
    def extract_cosigner_details(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract co-signer/guarantor details from text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with co-signer details and confidence score, or None
        """
        cosigner_info = {}
        
        # Extract name
        for pattern in self.cosigner_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                if len(name) > 3 and not any(char.isdigit() for char in name):
                    cosigner_info['name'] = name
                    cosigner_info['confidence'] = 0.8
                    cosigner_info['source_text'] = match.group(0)
                    break
            if 'name' in cosigner_info:
                break
        
        # Extract relationship
        for pattern in self.relationship_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                relationship = match.group(1).strip().lower()
                cosigner_info['relationship'] = relationship
                break
        
        return cosigner_info if cosigner_info else None
    
    def extract_collateral_details(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract collateral/security details from text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with collateral details and confidence score, or None
        """
        text_lower = text.lower()
        
        # Check if loan is unsecured
        if 'unsecured' in text_lower or 'no collateral' in text_lower:
            return {
                'type': 'unsecured',
                'description': 'No collateral required',
                'confidence': 0.9
            }
        
        # Extract collateral details
        for pattern in self.collateral_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                collateral_desc = match.group(1).strip()
                
                # Determine collateral type
                collateral_type = 'other'
                if 'property' in collateral_desc.lower() or 'house' in collateral_desc.lower():
                    collateral_type = 'property'
                elif 'gold' in collateral_desc.lower():
                    collateral_type = 'gold'
                elif 'vehicle' in collateral_desc.lower() or 'car' in collateral_desc.lower():
                    collateral_type = 'vehicle'
                elif 'land' in collateral_desc.lower():
                    collateral_type = 'land'
                
                return {
                    'type': collateral_type,
                    'description': collateral_desc,
                    'confidence': 0.75,
                    'source_text': match.group(0)
                }
        
        return None
    
    def extract_lender_info(self, text: str) -> Dict[str, Any]:
        """
        Extract complete lender information.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary containing bank name and branch details
        """
        bank_info = self.extract_bank_name(text)
        branch_info = self.extract_branch_details(text)
        
        result = {}
        if bank_info:
            result['bank_name'] = bank_info['bank_name']
            result['bank_confidence'] = bank_info['confidence']
        
        if branch_info:
            result['branch_name'] = branch_info['branch_name']
            result['branch_confidence'] = branch_info['confidence']
        
        return result
    
    def extract_all_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract all entity information from text.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary containing all extracted entity information
        """
        return {
            'lender': self.extract_lender_info(text),
            'cosigner': self.extract_cosigner_details(text),
            'collateral': self.extract_collateral_details(text)
        }
