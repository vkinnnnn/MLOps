"""
Normalization module for loan document data.

This module provides data models, output generation, and comparison
metrics calculation for structured loan data.
"""

from .data_models import (
    LoanType,
    DocumentMetadata,
    BankInfo,
    CoSignerDetails,
    FeeItem,
    PaymentScheduleEntry,
    TableData,
    NormalizedLoanData,
    ComparisonMetrics,
    ComparisonResult
)

from .output_generator import JSONOutputGenerator
from .comparison_calculator import ComparisonMetricsCalculator
from .comparison_service import ComparisonService
from .output_service import OutputService

__all__ = [
    # Enums
    'LoanType',
    
    # Data Models
    'DocumentMetadata',
    'BankInfo',
    'CoSignerDetails',
    'FeeItem',
    'PaymentScheduleEntry',
    'TableData',
    'NormalizedLoanData',
    'ComparisonMetrics',
    'ComparisonResult',
    
    # Services
    'JSONOutputGenerator',
    'ComparisonMetricsCalculator',
    'ComparisonService',
    'OutputService',
]
