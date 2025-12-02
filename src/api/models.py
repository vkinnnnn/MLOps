"""
Data models for the Student Loan Document Extractor Platform
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID


class LoanType(str, Enum):
    """Loan type enumeration"""
    EDUCATION = "education"
    HOME = "home"
    PERSONAL = "personal"
    VEHICLE = "vehicle"
    GOLD = "gold"
    OTHER = "other"


class ProcessingStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentMetadata(BaseModel):
    """Document metadata model"""
    document_id: str
    file_name: str
    file_type: str  # pdf, jpeg, png, tiff
    upload_timestamp: datetime
    file_size_bytes: int
    page_count: Optional[int] = None
    storage_path: str
    processing_status: ProcessingStatus = ProcessingStatus.PENDING


class BankInfo(BaseModel):
    """Bank information model"""
    bank_name: str
    branch_name: Optional[str] = None
    bank_code: Optional[str] = None


class CoSignerDetails(BaseModel):
    """Co-signer details model"""
    name: str
    relationship: str
    contact: Optional[str] = None


class FeeItem(BaseModel):
    """Fee item model"""
    fee_type: str  # processing, administrative, documentation
    amount: float
    currency: str = "INR"
    conditions: Optional[str] = None


class PaymentScheduleEntry(BaseModel):
    """Payment schedule entry model"""
    payment_number: int
    payment_date: Optional[datetime] = None
    total_amount: float
    principal_component: Optional[float] = None
    interest_component: Optional[float] = None
    outstanding_balance: Optional[float] = None


class TableData(BaseModel):
    """Table data model"""
    table_id: str
    headers: List[str]
    rows: List[List[str]]
    nested_columns: Optional[Dict[str, List[str]]] = None
    table_type: str  # payment_schedule, fee_structure, other


class NormalizedLoanData(BaseModel):
    """Normalized loan data model"""
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
    fees: List[FeeItem] = []
    processing_fee: Optional[float] = None
    late_payment_penalty: Optional[str] = None
    prepayment_penalty: Optional[str] = None
    
    # Repayment details
    repayment_mode: Optional[str] = None  # EMI, bullet, step-up
    payment_schedule: Optional[List[PaymentScheduleEntry]] = None
    
    # Additional details
    co_signer: Optional[CoSignerDetails] = None
    collateral_details: Optional[str] = None
    disbursement_terms: Optional[str] = None
    
    # Metadata
    extraction_confidence: Optional[float] = None  # 0.0 to 1.0
    extraction_timestamp: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class ComparisonMetrics(BaseModel):
    """Comparison metrics model"""
    loan_id: str
    total_cost_estimate: Optional[float] = None
    effective_interest_rate: Optional[float] = None
    flexibility_score: Optional[float] = None  # 0.0 to 10.0
    monthly_emi: Optional[float] = None
    total_interest_payable: Optional[float] = None


class ComparisonResult(BaseModel):
    """Comparison result model"""
    loans: List[NormalizedLoanData]
    metrics: List[ComparisonMetrics]
    best_by_cost: Optional[str] = None  # loan_id
    best_by_flexibility: Optional[str] = None  # loan_id
    comparison_notes: Dict[str, str] = {}


class QueryFilters(BaseModel):
    """Query filters for loan search"""
    loan_type: Optional[LoanType] = None
    bank_name: Optional[str] = None
    min_principal: Optional[float] = None
    max_principal: Optional[float] = None
    min_interest_rate: Optional[float] = None
    max_interest_rate: Optional[float] = None
    min_tenure_months: Optional[int] = None
    max_tenure_months: Optional[int] = None
    limit: int = 100
    offset: int = 0


class ProcessingJob(BaseModel):
    """Processing job model"""
    job_id: str
    status: str  # queued, processing, completed, failed
    total_documents: int
    processed_documents: int = 0
    failed_documents: int = 0
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
