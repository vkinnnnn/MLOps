"""
Data extraction module for loan documents.
Provides extractors for core loan terms, fees, entities, schedules, and additional terms.
"""

from .extraction_service import DataExtractionService
from .field_extractor import CoreLoanFieldExtractor
from .fee_extractor import FeeAndPenaltyExtractor
from .entity_extractor import EntityExtractor
from .schedule_extractor import PaymentScheduleExtractor
from .terms_extractor import AdditionalTermsExtractor
from .confidence_scorer import ConfidenceScorer

__all__ = [
    'DataExtractionService',
    'CoreLoanFieldExtractor',
    'FeeAndPenaltyExtractor',
    'EntityExtractor',
    'PaymentScheduleExtractor',
    'AdditionalTermsExtractor',
    'ConfidenceScorer'
]
