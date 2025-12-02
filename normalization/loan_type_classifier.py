"""
Loan Type Classifier Module

This module implements rule-based classification for different loan types
including education, home, personal, vehicle, and gold loans.
"""

import re
from typing import Dict, Optional, List, Tuple
from enum import Enum


class LoanType(str, Enum):
    """Enumeration of supported loan types"""
    EDUCATION = "education"
    HOME = "home"
    PERSONAL = "personal"
    VEHICLE = "vehicle"
    GOLD = "gold"
    OTHER = "other"


class LoanTypeClassifier:
    """
    Rule-based classifier for identifying loan types from document text.
    
    Uses keyword matching and pattern recognition to classify loans into
    education, home, personal, vehicle, gold, or other categories.
    """
    
    def __init__(self):
        """Initialize the classifier with keyword patterns for each loan type"""
        self.loan_type_keywords = {
            LoanType.EDUCATION: [
                r'\beducation\s+loan\b',
                r'\bstudent\s+loan\b',
                r'\btuition\s+fee',
                r'\bacademic\s+loan\b',
                r'\bscholarship\b',
                r'\buniversity\b',
                r'\bcollege\b',
                r'\beducational\s+institution\b',
                r'\bcourse\s+fee\b',
                r'\bstudent\s+finance\b',
            ],
            LoanType.HOME: [
                r'\bhome\s+loan\b',
                r'\bhousing\s+loan\b',
                r'\bmortgage\b',
                r'\bproperty\s+loan\b',
                r'\breal\s+estate\b',
                r'\bresidential\s+loan\b',
                r'\bhome\s+purchase\b',
                r'\bhouse\s+loan\b',
                r'\bproperty\s+purchase\b',
                r'\bhome\s+construction\b',
            ],
            LoanType.PERSONAL: [
                r'\bpersonal\s+loan\b',
                r'\bunsecured\s+loan\b',
                r'\bconsumer\s+loan\b',
                r'\bpersonal\s+finance\b',
                r'\bquick\s+loan\b',
                r'\binstant\s+loan\b',
            ],
            LoanType.VEHICLE: [
                r'\bvehicle\s+loan\b',
                r'\bcar\s+loan\b',
                r'\bauto\s+loan\b',
                r'\bautomobile\s+loan\b',
                r'\btwo\s+wheeler\b',
                r'\bfour\s+wheeler\b',
                r'\bbike\s+loan\b',
                r'\bmotor\s+vehicle\b',
                r'\bvehicle\s+finance\b',
            ],
            LoanType.GOLD: [
                r'\bgold\s+loan\b',
                r'\bgold\s+pledge\b',
                r'\bgold\s+backed\b',
                r'\bgold\s+collateral\b',
                r'\bjewel\s+loan\b',
                r'\bgold\s+ornament\b',
            ],
        }
        
        # Loan-type-specific field patterns
        self.specific_field_patterns = {
            LoanType.EDUCATION: {
                'institution_name': [
                    r'(?:university|college|institution)[\s:]+([A-Z][A-Za-z\s&,]+)',
                    r'educational\s+institution[\s:]+([A-Z][A-Za-z\s&,]+)',
                ],
                'course_name': [
                    r'course[\s:]+([A-Z][A-Za-z\s&,]+)',
                    r'program[\s:]+([A-Z][A-Za-z\s&,]+)',
                ],
                'student_name': [
                    r'student[\s\']?s?\s+name[\s:]+([A-Z][A-Za-z\s\.]+)',
                    r'borrower[\s\']?s?\s+name[\s:]+([A-Z][A-Za-z\s\.]+)',
                ],
            },
            LoanType.HOME: {
                'property_address': [
                    r'property\s+address[\s:]+([A-Za-z0-9\s,\.\-]+)',
                    r'property\s+location[\s:]+([A-Za-z0-9\s,\.\-]+)',
                ],
                'property_value': [
                    r'property\s+value[\s:]+(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{2})?)',
                    r'market\s+value[\s:]+(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{2})?)',
                ],
                'property_type': [
                    r'property\s+type[\s:]+(\w+)',
                    r'type\s+of\s+property[\s:]+(\w+)',
                ],
            },
            LoanType.VEHICLE: {
                'vehicle_make': [
                    r'make[\s:]+([A-Za-z]+)',
                    r'manufacturer[\s:]+([A-Za-z]+)',
                ],
                'vehicle_model': [
                    r'model[\s:]+([A-Za-z0-9\s]+)',
                ],
                'vehicle_year': [
                    r'year[\s:]+(\d{4})',
                    r'manufacturing\s+year[\s:]+(\d{4})',
                ],
                'vehicle_type': [
                    r'vehicle\s+type[\s:]+([A-Za-z\s]+)',
                ],
            },
            LoanType.GOLD: {
                'gold_weight': [
                    r'gold\s+weight[\s:]+(\d+(?:\.\d+)?)\s*(?:grams?|gms?)',
                    r'weight[\s:]+(\d+(?:\.\d+)?)\s*(?:grams?|gms?)',
                ],
                'gold_purity': [
                    r'purity[\s:]+(\d+)\s*(?:carat|kt)',
                    r'gold\s+purity[\s:]+(\d+)\s*(?:carat|kt)',
                ],
                'gold_value': [
                    r'gold\s+value[\s:]+(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{2})?)',
                    r'ornament\s+value[\s:]+(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{2})?)',
                ],
            },
            LoanType.PERSONAL: {
                'purpose': [
                    r'purpose[\s:]+([A-Za-z\s]+)',
                    r'loan\s+purpose[\s:]+([A-Za-z\s]+)',
                ],
            },
        }
    
    def classify_loan_type(self, text: str) -> Tuple[LoanType, float]:
        """
        Classify the loan type based on document text.
        
        Args:
            text: Extracted text from the loan document
            
        Returns:
            Tuple of (LoanType, confidence_score)
        """
        text_lower = text.lower()
        scores = {loan_type: 0 for loan_type in LoanType}
        
        # Count keyword matches for each loan type
        for loan_type, patterns in self.loan_type_keywords.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                scores[loan_type] += len(matches)
        
        # Find the loan type with highest score
        max_score = max(scores.values())
        
        if max_score == 0:
            return LoanType.OTHER, 0.0
        
        # Get the loan type with highest score
        classified_type = max(scores, key=scores.get)
        
        # Calculate confidence based on score distribution
        total_score = sum(scores.values())
        confidence = max_score / total_score if total_score > 0 else 0.0
        
        # Boost confidence if multiple keywords match
        if max_score >= 3:
            confidence = min(confidence * 1.2, 1.0)
        
        return classified_type, confidence
    
    def extract_loan_specific_fields(
        self, 
        text: str, 
        loan_type: LoanType
    ) -> Dict[str, Optional[str]]:
        """
        Extract loan-type-specific fields from document text.
        
        Args:
            text: Extracted text from the loan document
            loan_type: Classified loan type
            
        Returns:
            Dictionary of extracted loan-specific fields
        """
        specific_fields = {}
        
        if loan_type not in self.specific_field_patterns:
            return specific_fields
        
        patterns = self.specific_field_patterns[loan_type]
        
        for field_name, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    specific_fields[field_name] = match.group(1).strip()
                    break
            
            # Set to None if not found
            if field_name not in specific_fields:
                specific_fields[field_name] = None
        
        return specific_fields
    
    def classify_and_extract(self, text: str) -> Dict:
        """
        Classify loan type and extract loan-specific fields in one operation.
        
        Args:
            text: Extracted text from the loan document
            
        Returns:
            Dictionary containing loan_type, confidence, and specific_fields
        """
        loan_type, confidence = self.classify_loan_type(text)
        specific_fields = self.extract_loan_specific_fields(text, loan_type)
        
        return {
            'loan_type': loan_type.value,
            'classification_confidence': confidence,
            'loan_specific_fields': specific_fields,
        }
