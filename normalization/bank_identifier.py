"""
Bank Format Identifier Module

This module identifies lending institutions from loan documents and handles
bank-specific format variations and terminology normalization.
"""

import re
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class BankInfo:
    """Data class for bank information"""
    bank_name: str
    branch_name: Optional[str] = None
    bank_code: Optional[str] = None
    confidence: float = 0.0


class BankFormatIdentifier:
    """
    Identifies lending institutions and handles bank-specific format variations.
    
    Extracts bank name, branch details, and normalizes terminology across
    different banking institutions.
    """
    
    def __init__(self):
        """Initialize the identifier with bank patterns and terminology mappings"""
        
        # Major Indian banks and their variations
        self.bank_patterns = {
            'State Bank of India': [
                r'\bSBI\b',
                r'\bState\s+Bank\s+of\s+India\b',
                r'\bStateBank\b',
            ],
            'HDFC Bank': [
                r'\bHDFC\s+Bank\b',
                r'\bHDFC\b',
                r'\bHousing\s+Development\s+Finance\s+Corporation\b',
            ],
            'ICICI Bank': [
                r'\bICICI\s+Bank\b',
                r'\bICICI\b',
            ],
            'Axis Bank': [
                r'\bAxis\s+Bank\b',
                r'\bAxis\b',
            ],
            'Punjab National Bank': [
                r'\bPNB\b',
                r'\bPunjab\s+National\s+Bank\b',
            ],
          
  'Bank of Baroda': [
                r'\bBank\s+of\s+Baroda\b',
                r'\bBoB\b',
            ],
            'Canara Bank': [
                r'\bCanara\s+Bank\b',
            ],
            'Union Bank of India': [
                r'\bUnion\s+Bank\s+of\s+India\b',
                r'\bUnion\s+Bank\b',
            ],
            'Bank of India': [
                r'\bBank\s+of\s+India\b',
                r'\bBoI\b',
            ],
            'Indian Bank': [
                r'\bIndian\s+Bank\b',
            ],
            'Kotak Mahindra Bank': [
                r'\bKotak\s+Mahindra\s+Bank\b',
                r'\bKotak\s+Bank\b',
                r'\bKotak\b',
            ],
            'IndusInd Bank': [
                r'\bIndusInd\s+Bank\b',
                r'\bIndusInd\b',
            ],
            'Yes Bank': [
                r'\bYes\s+Bank\b',
            ],
            'IDFC First Bank': [
                r'\bIDFC\s+First\s+Bank\b',
                r'\bIDFC\s+Bank\b',
                r'\bIDFC\b',
            ],
            'Federal Bank': [
                r'\bFederal\s+Bank\b',
            ],
            'RBL Bank': [
                r'\bRBL\s+Bank\b',
                r'\bRatnakar\s+Bank\b',
            ],
            'South Indian Bank': [
                r'\bSouth\s+Indian\s+Bank\b',
            ],
            'Karur Vysya Bank': [
                r'\bKarur\s+Vysya\s+Bank\b',
                r'\bKVB\b',
            ],
            'Tamilnad Mercantile Bank': [
                r'\bTamilnad\s+Mercantile\s+Bank\b',
                r'\bTMB\b',
            ],
            'City Union Bank': [
                r'\bCity\s+Union\s+Bank\b',
                r'\bCUB\b',
            ],
        }
        
        # Terminology normalization mappings
        self.terminology_mappings = {
            # Interest rate terms
            'interest_rate': [
                'rate of interest',
                'interest rate',
                'roi',
                'annual interest rate',
                'interest p.a.',
                'interest per annum',
                'lending rate',
            ],
            # Principal amount terms
            'principal': [
                'loan amount',
                'principal amount',
                'sanctioned amount',
                'disbursed amount',
                'loan principal',
                'amount financed',
            ],
            # Tenure terms
            'tenure': [
                'loan tenure',
                'loan period',
                'repayment period',
                'loan term',
                'duration',
                'loan duration',
            ],
            # EMI terms
            'emi': [
                'emi',
                'equated monthly installment',
                'monthly installment',
                'monthly payment',
                'installment amount',
            ],
            # Processing fee terms
            'processing_fee': [
                'processing fee',
                'processing charges',
                'loan processing fee',
                'upfront fee',
                'application fee',
            ],
            # Prepayment terms
            'prepayment': [
                'prepayment',
                'pre-payment',
                'foreclosure',
                'early repayment',
                'advance payment',
            ],
        }
        
        # Bank-specific field name variations
        self.bank_field_variations = {
            'HDFC Bank': {
                'loan_account_number': 'loan account no',
                'customer_id': 'customer id',
            },
            'ICICI Bank': {
                'loan_account_number': 'loan a/c no',
                'customer_id': 'cif number',
            },
            'SBI': {
                'loan_account_number': 'loan account number',
                'customer_id': 'cif',
            },
        }
    
    def identify_bank(self, text: str) -> BankInfo:
        """
        Identify the lending institution from document text.
        
        Args:
            text: Extracted text from the loan document
            
        Returns:
            BankInfo object with bank details and confidence score
        """
        best_match = None
        best_confidence = 0.0
        match_positions = []
        
        # Search for bank patterns
        for bank_name, patterns in self.bank_patterns.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                if matches:
                    # Calculate confidence based on number of matches and position
                    confidence = len(matches) * 0.3
                    
                    # Boost confidence if found in first 500 characters (likely header)
                    if matches[0].start() < 500:
                        confidence += 0.4
                    
                    # Boost confidence for exact bank name matches
                    if pattern == rf'\b{re.escape(bank_name)}\b':
                        confidence += 0.3
                    
                    confidence = min(confidence, 1.0)
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = bank_name
                        match_positions = [m.start() for m in matches]
        
        if best_match:
            # Try to extract branch information
            branch_name = self._extract_branch_name(text, match_positions)
            bank_code = self._extract_bank_code(text)
            
            return BankInfo(
                bank_name=best_match,
                branch_name=branch_name,
                bank_code=bank_code,
                confidence=best_confidence
            )
        
        # If no match found, try generic bank patterns
        generic_match = self._extract_generic_bank_name(text)
        if generic_match:
            return BankInfo(
                bank_name=generic_match,
                confidence=0.5
            )
        
        return BankInfo(
            bank_name="Unknown",
            confidence=0.0
        )
   
 
    def _extract_branch_name(self, text: str, bank_positions: List[int]) -> Optional[str]:
        """Extract branch name from text near bank name occurrences"""
        branch_patterns = [
            r'branch[\s:]+([A-Za-z\s]+?)(?:\n|,|\.)',
            r'branch\s+name[\s:]+([A-Za-z\s]+?)(?:\n|,|\.)',
            r'branch\s+office[\s:]+([A-Za-z\s]+?)(?:\n|,|\.)',
        ]
        
        # Search near bank name positions
        for pos in bank_positions[:2]:  # Check first 2 occurrences
            context = text[max(0, pos-100):min(len(text), pos+300)]
            for pattern in branch_patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        
        return None
    
    def _extract_bank_code(self, text: str) -> Optional[str]:
        """Extract bank code (IFSC, SWIFT, etc.) from text"""
        code_patterns = [
            r'IFSC[\s:]+([A-Z]{4}0[A-Z0-9]{6})',
            r'IFSC\s+Code[\s:]+([A-Z]{4}0[A-Z0-9]{6})',
            r'SWIFT[\s:]+([A-Z]{8}|[A-Z]{11})',
        ]
        
        for pattern in code_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_generic_bank_name(self, text: str) -> Optional[str]:
        """Extract bank name using generic patterns"""
        generic_patterns = [
            r'([A-Z][A-Za-z\s]+Bank)',
            r'([A-Z][A-Za-z\s]+Financial\s+Services)',
            r'([A-Z][A-Za-z\s]+Finance)',
        ]
        
        for pattern in generic_patterns:
            match = re.search(pattern, text[:1000])  # Search in first 1000 chars
            if match:
                bank_name = match.group(1).strip()
                # Validate it's not a common false positive
                if len(bank_name) > 5 and 'loan' not in bank_name.lower():
                    return bank_name
        
        return None
    
    def normalize_terminology(
        self, 
        field_name: str, 
        bank_name: Optional[str] = None
    ) -> str:
        """
        Normalize bank-specific field terminology to standard names.
        
        Args:
            field_name: Original field name from document
            bank_name: Name of the bank (optional)
            
        Returns:
            Normalized field name
        """
        field_lower = field_name.lower().strip()
        
        # Check standard terminology mappings
        for standard_name, variations in self.terminology_mappings.items():
            if field_lower in [v.lower() for v in variations]:
                return standard_name
        
        # Check bank-specific variations
        if bank_name and bank_name in self.bank_field_variations:
            bank_variations = self.bank_field_variations[bank_name]
            for standard_name, variation in bank_variations.items():
                if field_lower == variation.lower():
                    return standard_name
        
        # Return original if no mapping found
        return field_name
    
    def get_bank_specific_patterns(self, bank_name: str) -> Dict[str, List[str]]:
        """
        Get bank-specific extraction patterns.
        
        Args:
            bank_name: Name of the bank
            
        Returns:
            Dictionary of field patterns specific to the bank
        """
        # This can be extended with bank-specific extraction patterns
        # For now, return empty dict as base implementation
        return {}
    
    def identify_and_normalize(self, text: str, extracted_fields: Dict) -> Dict:
        """
        Identify bank and normalize all field names in one operation.
        
        Args:
            text: Extracted text from the loan document
            extracted_fields: Dictionary of extracted fields with original names
            
        Returns:
            Dictionary with bank_info and normalized_fields
        """
        bank_info = self.identify_bank(text)
        
        normalized_fields = {}
        for field_name, field_value in extracted_fields.items():
            normalized_name = self.normalize_terminology(field_name, bank_info.bank_name)
            normalized_fields[normalized_name] = field_value
        
        return {
            'bank_info': {
                'bank_name': bank_info.bank_name,
                'branch_name': bank_info.branch_name,
                'bank_code': bank_info.bank_code,
                'identification_confidence': bank_info.confidence,
            },
            'normalized_fields': normalized_fields,
        }
