"""
Custom exceptions for the Student Loan Intelligence System.

Following KIRO Global Steering Guidelines for proper error handling.
"""

from typing import Optional, Any, Dict


class StudentLoanException(Exception):
    """
    Base exception for the Student Loan Intelligence System.
    
    All custom exceptions should inherit from this base class
    for consistent error handling across the application.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message='{self.message}', error_code='{self.error_code}')"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(StudentLoanException):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        constraint: Optional[str] = None,
    ):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        if constraint:
            details["constraint"] = constraint
            
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details
        )
        self.field = field
        self.value = value
        self.constraint = constraint


class ProcessingError(StudentLoanException):
    """Raised when document processing fails."""
    
    def __init__(
        self,
        message: str,
        document_id: Optional[str] = None,
        stage: Optional[str] = None,
        original_exception: Optional[Exception] = None,
    ):
        details = {}
        if document_id:
            details["document_id"] = document_id
        if stage:
            details["processing_stage"] = stage
        if original_exception:
            details["original_error"] = str(original_exception)
            
        super().__init__(
            message=message,
            error_code="PROCESSING_ERROR",
            details=details
        )
        self.document_id = document_id
        self.stage = stage
        self.original_exception = original_exception


class ServiceError(StudentLoanException):
    """Raised when external service calls fail."""
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        details = {}
        if service_name:
            details["service"] = service_name
        if status_code:
            details["status_code"] = status_code
        if response_data:
            details["response"] = response_data
            
        super().__init__(
            message=message,
            error_code="SERVICE_ERROR",
            details=details
        )
        self.service_name = service_name
        self.status_code = status_code
        self.response_data = response_data


class ConfigurationError(StudentLoanException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        expected_type: Optional[str] = None,
    ):
        details = {}
        if config_key:
            details["config_key"] = config_key
        if expected_type:
            details["expected_type"] = expected_type
            
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details
        )
        self.config_key = config_key
        self.expected_type = expected_type


class DatabaseError(StudentLoanException):
    """Raised when database operations fail."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        original_exception: Optional[Exception] = None,
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table
        if original_exception:
            details["original_error"] = str(original_exception)
            
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details
        )
        self.operation = operation
        self.table = table
        self.original_exception = original_exception


class AuthenticationError(StudentLoanException):
    """Raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        user_id: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        details = {}
        if user_id:
            details["user_id"] = user_id
        if reason:
            details["reason"] = reason
            
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details
        )
        self.user_id = user_id
        self.reason = reason


class AuthorizationError(StudentLoanException):
    """Raised when user lacks permission for an operation."""
    
    def __init__(
        self,
        message: str = "Access denied",
        user_id: Optional[str] = None,
        required_permission: Optional[str] = None,
    ):
        details = {}
        if user_id:
            details["user_id"] = user_id
        if required_permission:
            details["required_permission"] = required_permission
            
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details
        )
        self.user_id = user_id
        self.required_permission = required_permission


class RateLimitExceededError(StudentLoanException):
    """Raised when API rate limits are exceeded."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        limit_type: Optional[str] = None,
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        if limit_type:
            details["limit_type"] = limit_type
            
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details
        )
        self.retry_after = retry_after
        self.limit_type = limit_type


class FileHandlingError(StudentLoanException):
    """Raised when file operations fail."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None,
    ):
        details = {}
        if file_path:
            details["file_path"] = file_path
        if operation:
            details["operation"] = operation
        if original_exception:
            details["original_error"] = str(original_exception)
            
        super().__init__(
            message=message,
            error_code="FILE_HANDLING_ERROR",
            details=details
        )
        self.file_path = file_path
        self.operation = operation
        self.original_exception = original_exception


class ModelError(StudentLoanException):
    """Raised when AI model operations fail."""
    
    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        model_provider: Optional[str] = None,
        original_exception: Optional[Exception] = None,
    ):
        details = {}
        if model_name:
            details["model_name"] = model_name
        if model_provider:
            details["model_provider"] = model_provider
        if original_exception:
            details["original_error"] = str(original_exception)
            
        super().__init__(
            message=message,
            error_code="MODEL_ERROR",
            details=details
        )
        self.model_name = model_name
        self.model_provider = model_provider
        self.original_exception = original_exception
