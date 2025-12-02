"""
Global error handlers and exception handling for the API.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from typing import Union

from src.api.models import ErrorResponse

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions and return user-friendly error messages.
    """
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail} - Path: {request.url.path}")
    
    error_response = ErrorResponse(
        success=False,
        error_type="http_error",
        message=str(exc.detail),
        details={
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle request validation errors and return detailed error information.
    """
    logger.error(f"Validation error: {exc.errors()} - Path: {request.url.path}")
    
    error_response = ErrorResponse(
        success=False,
        error_type="validation_error",
        message="Request validation failed",
        details={
            "errors": exc.errors(),
            "path": str(request.url.path)
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions and return generic error message.
    """
    logger.exception(f"Unexpected error: {str(exc)} - Path: {request.url.path}")
    
    error_response = ErrorResponse(
        success=False,
        error_type="internal_error",
        message="An unexpected error occurred. Please try again later.",
        details={
            "path": str(request.url.path)
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )


class ProcessingError(Exception):
    """Custom exception for document processing errors."""
    
    def __init__(self, error_type: str, message: str, document_id: str = None):
        self.error_type = error_type
        self.message = message
        self.document_id = document_id
        super().__init__(self.message)


class ValidationError(Exception):
    """Custom exception for data validation errors."""
    
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class StorageError(Exception):
    """Custom exception for storage-related errors."""
    
    def __init__(self, message: str, operation: str = None):
        self.message = message
        self.operation = operation
        super().__init__(self.message)


def get_user_friendly_message(error: Exception) -> str:
    """
    Convert technical error messages to user-friendly messages.
    """
    error_messages = {
        "OCR": "Unable to read text from the document. Please ensure the document is clear and readable.",
        "table": "Unable to extract table data. Please verify the document contains properly formatted tables.",
        "validation": "The extracted data does not meet required standards. Please check the document format.",
        "storage": "Unable to save the document. Please try again later.",
        "database": "Unable to access data. Please try again later.",
        "timeout": "Processing is taking longer than expected. Please try again later.",
    }
    
    error_str = str(error).lower()
    
    for key, message in error_messages.items():
        if key in error_str:
            return message
    
    return "An error occurred while processing your request. Please try again."
