"""
Normalization service for loan document data.

This service orchestrates the normalization pipeline: field mapping,
schema validation, and data standardization.
"""

from typing import Dict, Any, Optional
import logging
import uuid

from .data_models import NormalizedLoanData, ValidationResult
from .field_mapper import FieldMapper
from .schema_validator import SchemaValidator


logger = logging.getLogger(__name__)


class NormalizationService:
    """
    Service for normalizing extracted loan data to standardized schema.
    
    This service coordinates field mapping and schema validation to transform
    raw extracted data into validated NormalizedLoanData instances.
    """
    
    def __init__(self, strict_validation: bool = False):
        """
        Initialize the normalization service.
        
        Args:
            strict_validation: If True, treat warnings as validation errors
        """
        self.field_mapper = FieldMapper()
        self.schema_validator = SchemaValidator(strict_mode=strict_validation)
        self.strict_validation = strict_validation
    
    def normalize(
        self,
        extracted_data: Dict[str, Any],
        document_id: str,
        loan_id: Optional[str] = None
    ) -> ValidationResult:
        """
        Normalize extracted loan data.
        
        This method performs the complete normalization pipeline:
        1. Map extracted fields to standardized schema
        2. Validate against Pydantic models
        3. Apply business rule validations
        
        Args:
            extracted_data: Raw extracted data from extraction module
            document_id: ID of source document
            loan_id: Optional loan ID (generated if not provided)
            
        Returns:
            ValidationResult containing normalized data or errors
        """
        # Generate loan ID if not provided
        if not loan_id:
            loan_id = self._generate_loan_id()
        
        logger.info(f"Starting normalization for loan {loan_id}")
        
        try:
            # Step 1: Map fields to standardized schema
            logger.debug("Mapping fields to standardized schema")
            normalized_data = self.field_mapper.map_fields(
                extracted_data=extracted_data,
                document_id=document_id,
                loan_id=loan_id
            )
            
            # Get mapping warnings
            mapping_warnings = self.field_mapper.get_warnings()
            if mapping_warnings:
                logger.warning(f"Field mapping generated {len(mapping_warnings)} warnings")
                for warning in mapping_warnings:
                    logger.debug(f"  - {warning}")
            
            # Step 2: Validate against schema
            logger.debug("Validating against schema")
            validation_result = self.schema_validator.validate_loan_data(normalized_data)
            
            # Add mapping warnings to validation result
            validation_result.warnings.extend(mapping_warnings)
            
            # Log validation result
            if validation_result.is_valid:
                logger.info(f"Normalization successful for loan {loan_id}")
                if validation_result.warnings:
                    logger.info(f"  With {len(validation_result.warnings)} warnings")
            else:
                logger.error(f"Normalization failed for loan {loan_id}")
                logger.error(f"  {len(validation_result.errors)} validation errors")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Unexpected error during normalization: {e}", exc_info=True)
            
            # Return error result
            from .data_models import ValidationError
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(
                    field="general",
                    error_type="normalization_error",
                    message=str(e)
                )],
                warnings=[],
                validated_data=None
            )
    
    def normalize_batch(
        self,
        extracted_data_list: list[Dict[str, Any]],
        document_ids: list[str]
    ) -> list[ValidationResult]:
        """
        Normalize multiple extracted loan documents.
        
        Args:
            extracted_data_list: List of raw extracted data dictionaries
            document_ids: List of corresponding document IDs
            
        Returns:
            List of ValidationResult objects
        """
        if len(extracted_data_list) != len(document_ids):
            raise ValueError("Number of extracted data items must match number of document IDs")
        
        logger.info(f"Starting batch normalization for {len(extracted_data_list)} documents")
        
        results = []
        for extracted_data, document_id in zip(extracted_data_list, document_ids):
            result = self.normalize(extracted_data, document_id)
            results.append(result)
        
        # Log batch summary
        successful = sum(1 for r in results if r.is_valid)
        failed = len(results) - successful
        logger.info(f"Batch normalization complete: {successful} successful, {failed} failed")
        
        return results
    
    def validate_only(self, loan_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate loan data without field mapping.
        
        Use this when you already have data in the standardized format
        and just need validation.
        
        Args:
            loan_data: Dictionary in NormalizedLoanData format
            
        Returns:
            ValidationResult
        """
        return self.schema_validator.validate_loan_data(loan_data)
    
    def get_normalized_dict(self, validation_result: ValidationResult) -> Optional[Dict[str, Any]]:
        """
        Get normalized data as dictionary.
        
        Args:
            validation_result: ValidationResult from normalize()
            
        Returns:
            Dictionary representation of normalized data, or None if invalid
        """
        if not validation_result.is_valid or not validation_result.validated_data:
            return None
        
        return validation_result.validated_data.model_dump()
    
    def get_normalized_json(self, validation_result: ValidationResult) -> Optional[str]:
        """
        Get normalized data as JSON string.
        
        Args:
            validation_result: ValidationResult from normalize()
            
        Returns:
            JSON string representation of normalized data, or None if invalid
        """
        if not validation_result.is_valid or not validation_result.validated_data:
            return None
        
        return validation_result.validated_data.model_dump_json(indent=2)
    
    def _generate_loan_id(self) -> str:
        """Generate a unique loan ID."""
        return f"loan_{uuid.uuid4().hex[:12]}"
    
    def get_validation_summary(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """
        Get a summary of validation result.
        
        Args:
            validation_result: ValidationResult to summarize
            
        Returns:
            Dictionary with validation summary
        """
        summary = {
            'is_valid': validation_result.is_valid,
            'error_count': len(validation_result.errors),
            'warning_count': len(validation_result.warnings),
            'has_data': validation_result.validated_data is not None
        }
        
        if validation_result.errors:
            summary['errors'] = [
                {
                    'field': err.field,
                    'type': err.error_type,
                    'message': err.message
                }
                for err in validation_result.errors
            ]
        
        if validation_result.warnings:
            summary['warnings'] = validation_result.warnings
        
        return summary


# Convenience functions for common use cases

def normalize_loan_data(
    extracted_data: Dict[str, Any],
    document_id: str,
    loan_id: Optional[str] = None,
    strict: bool = False
) -> ValidationResult:
    """
    Convenience function to normalize loan data.
    
    Args:
        extracted_data: Raw extracted data
        document_id: Source document ID
        loan_id: Optional loan ID
        strict: Whether to use strict validation
        
    Returns:
        ValidationResult
    """
    service = NormalizationService(strict_validation=strict)
    return service.normalize(extracted_data, document_id, loan_id)


def quick_normalize(
    extracted_data: Dict[str, Any],
    document_id: str
) -> Optional[NormalizedLoanData]:
    """
    Quick normalization that returns data or None.
    
    Args:
        extracted_data: Raw extracted data
        document_id: Source document ID
        
    Returns:
        NormalizedLoanData if successful, None otherwise
    """
    result = normalize_loan_data(extracted_data, document_id)
    return result.validated_data if result.is_valid else None
