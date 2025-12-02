"""
Schema validator for loan data using Pydantic models.

This module validates extracted and normalized loan data against the defined
Pydantic schemas, providing detailed error reporting and graceful error handling.
"""

from typing import Dict, Any, List, Optional
from pydantic import ValidationError as PydanticValidationError
import logging

from .data_models import (
    NormalizedLoanData, ValidationResult, ValidationError,
    BankInfo, CoSignerDetails, FeeItem, PaymentScheduleEntry,
    ComparisonMetrics, ComparisonResult
)


logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates loan data against Pydantic schemas."""
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize the schema validator.
        
        Args:
            strict_mode: If True, treat warnings as errors
        """
        self.strict_mode = strict_mode
        self.validation_errors: List[ValidationError] = []
        self.warnings: List[str] = []
    
    def validate_loan_data(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate loan data against NormalizedLoanData schema.
        
        Args:
            data: Dictionary containing loan data to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        self.validation_errors = []
        self.warnings = []
        
        try:
            # Attempt to create NormalizedLoanData instance
            validated_loan = NormalizedLoanData(**data)
            
            # Perform additional business logic validations
            self._validate_business_rules(validated_loan)
            
            # If strict mode and there are warnings, treat as failure
            if self.strict_mode and self.warnings:
                return ValidationResult(
                    is_valid=False,
                    errors=[ValidationError(
                        field="general",
                        error_type="strict_mode_warning",
                        message=warning
                    ) for warning in self.warnings],
                    warnings=self.warnings,
                    validated_data=None
                )
            
            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=self.warnings,
                validated_data=validated_loan
            )
            
        except PydanticValidationError as e:
            # Parse Pydantic validation errors
            errors = self._parse_pydantic_errors(e)
            
            logger.warning(f"Validation failed with {len(errors)} errors")
            
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=self.warnings,
                validated_data=None
            )
        
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected validation error: {e}")
            
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(
                    field="general",
                    error_type="unexpected_error",
                    message=str(e)
                )],
                warnings=self.warnings,
                validated_data=None
            )
    
    def validate_bank_info(self, data: Dict[str, Any]) -> Optional[BankInfo]:
        """
        Validate bank information data.
        
        Args:
            data: Dictionary containing bank info
            
        Returns:
            BankInfo instance if valid, None otherwise
        """
        try:
            return BankInfo(**data)
        except PydanticValidationError as e:
            logger.warning(f"Bank info validation failed: {e}")
            return None
    
    def validate_co_signer(self, data: Dict[str, Any]) -> Optional[CoSignerDetails]:
        """
        Validate co-signer details.
        
        Args:
            data: Dictionary containing co-signer info
            
        Returns:
            CoSignerDetails instance if valid, None otherwise
        """
        try:
            return CoSignerDetails(**data)
        except PydanticValidationError as e:
            logger.warning(f"Co-signer validation failed: {e}")
            return None
    
    def validate_fee_item(self, data: Dict[str, Any]) -> Optional[FeeItem]:
        """
        Validate fee item data.
        
        Args:
            data: Dictionary containing fee info
            
        Returns:
            FeeItem instance if valid, None otherwise
        """
        try:
            return FeeItem(**data)
        except PydanticValidationError as e:
            logger.warning(f"Fee item validation failed: {e}")
            return None
    
    def validate_payment_entry(self, data: Dict[str, Any]) -> Optional[PaymentScheduleEntry]:
        """
        Validate payment schedule entry.
        
        Args:
            data: Dictionary containing payment entry info
            
        Returns:
            PaymentScheduleEntry instance if valid, None otherwise
        """
        try:
            return PaymentScheduleEntry(**data)
        except PydanticValidationError as e:
            logger.warning(f"Payment entry validation failed: {e}")
            return None
    
    def validate_comparison_metrics(self, data: Dict[str, Any]) -> Optional[ComparisonMetrics]:
        """
        Validate comparison metrics data.
        
        Args:
            data: Dictionary containing comparison metrics
            
        Returns:
            ComparisonMetrics instance if valid, None otherwise
        """
        try:
            return ComparisonMetrics(**data)
        except PydanticValidationError as e:
            logger.warning(f"Comparison metrics validation failed: {e}")
            return None
    
    def validate_comparison_result(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate comparison result data.
        
        Args:
            data: Dictionary containing comparison result
            
        Returns:
            ValidationResult with validation status
        """
        try:
            validated_result = ComparisonResult(**data)
            
            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                validated_data=None  # ComparisonResult, not NormalizedLoanData
            )
            
        except PydanticValidationError as e:
            errors = self._parse_pydantic_errors(e)
            
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=[],
                validated_data=None
            )
    
    def _parse_pydantic_errors(self, error: PydanticValidationError) -> List[ValidationError]:
        """
        Parse Pydantic validation errors into ValidationError objects.
        
        Args:
            error: PydanticValidationError instance
            
        Returns:
            List of ValidationError objects
        """
        errors = []
        
        for err in error.errors():
            field_path = '.'.join(str(loc) for loc in err['loc'])
            error_type = err['type']
            message = err['msg']
            
            errors.append(ValidationError(
                field=field_path,
                error_type=error_type,
                message=message
            ))
        
        return errors
    
    def _validate_business_rules(self, loan_data: NormalizedLoanData) -> None:
        """
        Validate business logic rules beyond schema validation.
        
        Args:
            loan_data: Validated NormalizedLoanData instance
        """
        # Check if principal amount is reasonable
        if loan_data.principal_amount > 100000000:  # 10 crore
            self.warnings.append(
                f"Principal amount {loan_data.principal_amount} is unusually high"
            )
        
        if loan_data.principal_amount < 1000:  # 1000 rupees
            self.warnings.append(
                f"Principal amount {loan_data.principal_amount} is unusually low"
            )
        
        # Check if interest rate is reasonable
        if loan_data.interest_rate > 50:
            self.warnings.append(
                f"Interest rate {loan_data.interest_rate}% is unusually high"
            )
        
        if loan_data.interest_rate < 0.1:
            self.warnings.append(
                f"Interest rate {loan_data.interest_rate}% is unusually low"
            )
        
        # Check if tenure is reasonable
        if loan_data.tenure_months > 360:  # 30 years
            self.warnings.append(
                f"Tenure {loan_data.tenure_months} months is unusually long"
            )
        
        if loan_data.tenure_months < 1:
            self.warnings.append(
                f"Tenure {loan_data.tenure_months} months is too short"
            )
        
        # Check moratorium period
        if loan_data.moratorium_period_months:
            if loan_data.moratorium_period_months > loan_data.tenure_months:
                self.warnings.append(
                    "Moratorium period exceeds loan tenure"
                )
            
            if loan_data.moratorium_period_months > 60:  # 5 years
                self.warnings.append(
                    f"Moratorium period {loan_data.moratorium_period_months} months is unusually long"
                )
        
        # Check payment schedule consistency
        if loan_data.payment_schedule:
            self._validate_payment_schedule(loan_data)
        
        # Check fees reasonableness
        if loan_data.fees:
            total_fees = sum(fee.amount for fee in loan_data.fees)
            if total_fees > loan_data.principal_amount * 0.1:  # More than 10% of principal
                self.warnings.append(
                    f"Total fees {total_fees} exceed 10% of principal amount"
                )
        
        # Check extraction confidence
        if loan_data.extraction_confidence < 0.7:
            self.warnings.append(
                f"Low extraction confidence: {loan_data.extraction_confidence:.2f}"
            )
    
    def _validate_payment_schedule(self, loan_data: NormalizedLoanData) -> None:
        """
        Validate payment schedule consistency.
        
        Args:
            loan_data: NormalizedLoanData instance with payment schedule
        """
        schedule = loan_data.payment_schedule
        
        if not schedule:
            return
        
        # Check if payment numbers are sequential
        expected_number = 1
        for entry in schedule:
            if entry.payment_number != expected_number:
                self.warnings.append(
                    f"Payment schedule has non-sequential payment numbers"
                )
                break
            expected_number += 1
        
        # Check if number of payments matches tenure
        if len(schedule) != loan_data.tenure_months:
            self.warnings.append(
                f"Payment schedule has {len(schedule)} entries but tenure is {loan_data.tenure_months} months"
            )
        
        # Check if dates are in chronological order
        for i in range(1, len(schedule)):
            if schedule[i].payment_date <= schedule[i-1].payment_date:
                self.warnings.append(
                    f"Payment schedule dates are not in chronological order"
                )
                break
        
        # Check if outstanding balance decreases
        for i in range(1, len(schedule)):
            if schedule[i].outstanding_balance > schedule[i-1].outstanding_balance:
                self.warnings.append(
                    f"Outstanding balance increases in payment schedule"
                )
                break
        
        # Check if final balance is close to zero
        if schedule:
            final_balance = schedule[-1].outstanding_balance
            if final_balance > loan_data.principal_amount * 0.01:  # More than 1% remaining
                self.warnings.append(
                    f"Final outstanding balance {final_balance} is not close to zero"
                )
    
    def get_validation_summary(self, result: ValidationResult) -> str:
        """
        Generate a human-readable validation summary.
        
        Args:
            result: ValidationResult to summarize
            
        Returns:
            String summary of validation result
        """
        if result.is_valid:
            summary = "✓ Validation passed"
            if result.warnings:
                summary += f" with {len(result.warnings)} warning(s)"
            return summary
        else:
            summary = f"✗ Validation failed with {len(result.errors)} error(s)"
            if result.warnings:
                summary += f" and {len(result.warnings)} warning(s)"
            return summary
    
    def get_detailed_errors(self, result: ValidationResult) -> str:
        """
        Generate detailed error report.
        
        Args:
            result: ValidationResult to report on
            
        Returns:
            Formatted string with error details
        """
        if result.is_valid:
            return "No errors"
        
        lines = ["Validation Errors:"]
        for i, error in enumerate(result.errors, 1):
            lines.append(f"{i}. Field: {error.field}")
            lines.append(f"   Type: {error.error_type}")
            lines.append(f"   Message: {error.message}")
        
        if result.warnings:
            lines.append("\nWarnings:")
            for i, warning in enumerate(result.warnings, 1):
                lines.append(f"{i}. {warning}")
        
        return "\n".join(lines)


def validate_loan_data_quick(data: Dict[str, Any]) -> bool:
    """
    Quick validation check for loan data.
    
    Args:
        data: Dictionary containing loan data
        
    Returns:
        True if valid, False otherwise
    """
    validator = SchemaValidator()
    result = validator.validate_loan_data(data)
    return result.is_valid


def validate_and_log(data: Dict[str, Any], logger_instance: Optional[logging.Logger] = None) -> ValidationResult:
    """
    Validate loan data and log results.
    
    Args:
        data: Dictionary containing loan data
        logger_instance: Optional logger instance
        
    Returns:
        ValidationResult
    """
    log = logger_instance or logger
    
    validator = SchemaValidator()
    result = validator.validate_loan_data(data)
    
    summary = validator.get_validation_summary(result)
    log.info(summary)
    
    if not result.is_valid:
        details = validator.get_detailed_errors(result)
        log.warning(details)
    
    return result
