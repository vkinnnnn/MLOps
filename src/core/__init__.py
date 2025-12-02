"""
Core module for the Student Loan Intelligence System.

This module contains the fundamental components including configuration management,
exception handling, and core business logic.
"""

from .config import settings
from .exceptions import (
    StudentLoanException,
    ValidationError,
    ProcessingError,
    ServiceError,
    ConfigurationError,
)

__all__ = [
    "settings",
    "StudentLoanException",
    "ValidationError",
    "ProcessingError", 
    "ServiceError",
    "ConfigurationError",
]
