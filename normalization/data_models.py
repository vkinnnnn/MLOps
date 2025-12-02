"""
Data models for loan document extraction and normalization.

This module defines Pydantic models for structured loan data representation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class LoanType(str, Enum):
    """Enumeration of supported loan types."""
    EDUCATION = "education"
    HOME = "home"
    PERSONAL = "personal"
    VEHICLE = "vehicle"
    GOLD = "gold"
    OTHER = "other"


class DocumentMetadata(BaseModel):
    """Metadata for uploaded loan documents."""
    document_id: str
    file_name: str
    file_type: str  # pdf, jpeg, png, tiff
    upload_timestamp: datetime
    file_size_bytes: int
    page_count: int
    storage_path: str


class BankInfo(BaseModel):
    """Information about the lending institution."""
    bank_name: str
    branch_name: Optional[str] = None
    bank_code: Optional[str] = None


class CoSignerDetails(BaseModel):
    """Details about loan co-signer."""
    name: str
    relationship: str
    contact: Optional[str] = None


class FeeItem(BaseModel):
    """Individual fee or charge item."""
    fee_type: str  # processing, administrative, documentation
    amount: float
    currency: str = "INR"
    conditions: Optional[str] = None


class PaymentScheduleEntry(BaseModel):
    """Single entry in payment schedule."""
    payment_number: int
    payment_date: Optional[str] = None  # Date as string for flexibility
    total_amount: float
    principal_component: Optional[float] = None
    interest_component: Optional[float] = None
    outstanding_balance: Optional[float] = None


class TableData(BaseModel):
    """Structured table data extracted from document."""
    table_id: str
    headers: List[str]
    rows: List[List[str]]
    nested_columns: Optional[Dict[str, List[str]]] = None
    table_type: str  # payment_schedule, fee_structure, other


class NormalizedLoanData(BaseModel):
    """Complete normalized loan data structure."""
    loan_id: str
    document_id: str
    loan_type: LoanType
    bank_info: Optional[BankInfo] = None
    
    # Core loan terms
    principal_amount: Optional[float] = None
    currency: str = "INR"
    interest_rate: Optional[float] = None  # Annual percentage
    tenure_months: Optional[int] = None
    moratorium_period_months: Optional[int] = None
    
    # Fees and charges
    fees: List[FeeItem] = Field(default_factory=list)
    processing_fee: Optional[float] = None
    late_payment_penalty: Optional[str] = None
    prepayment_penalty: Optional[str] = None
    
    # Repayment details
    repayment_mode: Optional[str] = None  # EMI, bullet, step-up
    payment_schedule: List[PaymentScheduleEntry] = Field(default_factory=list)
    
    # Additional details
    co_signer: Optional[CoSignerDetails] = None
    collateral_details: Optional[str] = None
    disbursement_terms: Optional[str] = None
    
    # Tables extracted from document
    tables: List[TableData] = Field(default_factory=list)
    
    # Metadata
    extraction_confidence: float = 0.0  # 0.0 to 1.0
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    
    # Raw extracted fields for reference
    raw_extracted_fields: Dict[str, Any] = Field(default_factory=dict)


class ComparisonMetrics(BaseModel):
    """Calculated metrics for loan comparison."""
    loan_id: str
    total_cost_estimate: float
    effective_interest_rate: float
    flexibility_score: float  # 0.0 to 10.0
    monthly_emi: Optional[float] = None
    total_interest_payable: float
    calculation_timestamp: datetime = Field(default_factory=datetime.now)


class ComparisonResult(BaseModel):
    """Result of comparing multiple loans."""
    loans: List[NormalizedLoanData]
    metrics: List[ComparisonMetrics]
    best_by_cost: Optional[str] = None  # loan_id
    best_by_flexibility: Optional[str] = None  # loan_id
    comparison_notes: Dict[str, str] = Field(default_factory=dict)
