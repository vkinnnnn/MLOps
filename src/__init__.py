"""
Student Loan Intelligence System

A comprehensive AI-powered platform for student loan document processing,
comparison analysis, and educational guidance.

Following KIRO Global Steering Guidelines for development excellence.
"""

__version__ = "2.0.0"
__author__ = "Student Loan Intelligence Team"
__email__ = "team@student-loan-intelligence.com"
__description__ = "AI-powered student loan document processing and comparison platform"

# Core exports for external usage
from src.core.config import settings
from src.core.exceptions import (
    StudentLoanException,
    ValidationError,
    ProcessingError,
    ServiceError,
)

__all__ = [
    "settings",
    "StudentLoanException",
    "ValidationError", 
    "ProcessingError",
    "ServiceError",
]
