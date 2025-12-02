"""
Main extraction service that orchestrates all field extractors.
Provides a unified interface for extracting loan data from documents.
"""

from typing import Dict, Any, List, Optional
from .field_extractor import CoreLoanFieldExtractor
from .fee_extractor import FeeAndPenaltyExtractor
from .entity_extractor import EntityExtractor
from .schedule_extractor import PaymentScheduleExtractor
from .terms_extractor import AdditionalTermsExtractor
from .confidence_scorer import ConfidenceScorer


class DataExtractionService:
    """
    Main service for extracting structured loan data from OCR text and tables.
    Orchestrates all specialized extractors and provides confidence scoring.
    """
    
    def __init__(self):
        """Initialize all extractors."""
        self.core_extractor = CoreLoanFieldExtractor()
        self.fee_extractor = FeeAndPenaltyExtractor()
        self.entity_extractor = EntityExtractor()
        self.schedule_extractor = PaymentScheduleExtractor()
        self.terms_extractor = AdditionalTermsExtractor()
        self.confidence_scorer = ConfidenceScorer()
    
    def extract_loan_data(
        self, 
        text: str, 
        tables: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Extract all loan data from text and tables.
        
        Args:
            text: OCR extracted text from document
            tables: List of extracted table structures (optional)
            
        Returns:
            Dictionary containing all extracted loan data with confidence scores
        """
        # Extract core loan fields
        core_fields = self.core_extractor.extract_all_core_fields(text)
        
        # Extract fees and penalties
        fees_and_penalties = self.fee_extractor.extract_all_fees_and_penalties(text, tables)
        
        # Extract entity information
        entities = self.entity_extractor.extract_all_entities(text)
        
        # Extract payment schedule from tables
        payment_schedule = None
        if tables:
            payment_schedule = self.schedule_extractor.extract_schedule_from_tables(tables)
        
        # Extract additional terms
        additional_terms = self.terms_extractor.extract_all_additional_terms(text)
        
        # Compile all extracted data
        extracted_data = {
            'core_fields': core_fields,
            'fees': fees_and_penalties.get('fees', []),
            'penalties': fees_and_penalties.get('penalties', []),
            'entities': entities,
            'payment_schedule': payment_schedule,
            'additional_terms': additional_terms
        }
        
        # Calculate confidence scores
        confidence_report = self.confidence_scorer.generate_confidence_report(extracted_data)
        
        # Add confidence report to extracted data
        extracted_data['confidence_report'] = confidence_report
        
        return extracted_data
    
    def extract_core_fields_only(self, text: str) -> Dict[str, Any]:
        """
        Extract only core loan fields (principal, interest, tenure, moratorium).
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with core fields and confidence scores
        """
        core_fields = self.core_extractor.extract_all_core_fields(text)
        
        # Calculate confidence for core fields only
        extracted_data = {'core_fields': core_fields}
        confidence_report = self.confidence_scorer.generate_confidence_report(extracted_data)
        
        return {
            'core_fields': core_fields,
            'confidence_report': confidence_report
        }
    
    def extract_fees_and_penalties_only(
        self, 
        text: str, 
        tables: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Extract only fees and penalties.
        
        Args:
            text: OCR extracted text
            tables: List of extracted table structures (optional)
            
        Returns:
            Dictionary with fees and penalties
        """
        return self.fee_extractor.extract_all_fees_and_penalties(text, tables)
    
    def extract_payment_schedule_only(
        self, 
        tables: List[Dict[str, Any]]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Extract only payment schedule from tables.
        
        Args:
            tables: List of extracted table structures
            
        Returns:
            Payment schedule or None
        """
        return self.schedule_extractor.extract_schedule_from_tables(tables)
    
    def get_extraction_summary(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of extracted data.
        
        Args:
            extracted_data: Full extracted data dictionary
            
        Returns:
            Summary with key metrics and status
        """
        summary = {
            'extraction_status': 'success',
            'overall_confidence': extracted_data.get('confidence_report', {}).get('overall_confidence', 0),
            'confidence_level': extracted_data.get('confidence_report', {}).get('confidence_level', 'unknown'),
            'requires_review': extracted_data.get('confidence_report', {}).get('requires_review', True),
            'extracted_fields': {}
        }
        
        # Summarize core fields
        core = extracted_data.get('core_fields', {})
        summary['extracted_fields']['principal_amount'] = core.get('principal_amount', {}).get('value') if core.get('principal_amount') else None
        summary['extracted_fields']['interest_rate'] = core.get('interest_rate', {}).get('value') if core.get('interest_rate') else None
        summary['extracted_fields']['tenure_months'] = core.get('tenure', {}).get('value') if core.get('tenure') else None
        summary['extracted_fields']['moratorium_months'] = core.get('moratorium_period', {}).get('value') if core.get('moratorium_period') else None
        
        # Summarize entities
        entities = extracted_data.get('entities', {})
        lender = entities.get('lender', {})
        summary['extracted_fields']['bank_name'] = lender.get('bank_name')
        summary['extracted_fields']['branch_name'] = lender.get('branch_name')
        
        # Count fees and penalties
        summary['extracted_fields']['fees_count'] = len(extracted_data.get('fees', []))
        summary['extracted_fields']['penalties_count'] = len(extracted_data.get('penalties', []))
        
        # Payment schedule info
        schedule = extracted_data.get('payment_schedule')
        summary['extracted_fields']['payment_schedule_entries'] = len(schedule) if schedule else 0
        
        # Additional terms
        terms = extracted_data.get('additional_terms', {})
        summary['extracted_fields']['repayment_mode'] = terms.get('repayment_mode', {}).get('mode') if terms.get('repayment_mode') else None
        
        return summary
