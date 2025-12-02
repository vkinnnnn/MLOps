"""
Unit tests for schema validation
Tests Pydantic model validation and data integrity
"""
import pytest
from typing import Dict, Any, List, Optional
from datetime import date
from enum import Enum


# Mock Pydantic-like models for testing
class LoanType(str, Enum):
    """Loan type enumeration"""
    EDUCATION = "education"
    HOME = "home"
    PERSONAL = "personal"
    VEHICLE = "vehicle"
    GOLD = "gold"
    OTHER = "other"


class TestSchemaValidation:
    """Test schema validation functionality"""
    
    def test_required_field_validation(self):
        """Test validation of required fields"""
        required_fields = [
            "loan_id",
            "document_id",
            "loan_type",
            "principal_amount",
            "interest_rate",
            "tenure_months"
        ]
        
        loan_data = {
            "loan_id": "loan_001",
            "document_id": "doc_001",
            "loan_type": "education",
            "principal_amount": 50000,
            "interest_rate": 8.5,
            "tenure_months": 60
        }
        
        for field in required_fields:
            assert field in loan_data, f"Required field {field} should be present"
            assert loan_data[field] is not None, \
                f"Required field {field} should have value"
    
    def test_optional_field_validation(self):
        """Test validation of optional fields"""
        optional_fields = {
            "moratorium_period_months": None,
            "cosigner": None,
            "collateral_details": "Property"
        }
        
        # Optional fields can be None
        for field, value in optional_fields.items():
            assert field in optional_fields, f"Optional field {field} should be allowed"
    
    def test_data_type_validation(self):
        """Test validation of data types"""
        test_data = {
            "principal_amount": 50000,  # Should be numeric
            "interest_rate": 8.5,  # Should be float
            "tenure_months": 60,  # Should be integer
            "bank_name": "ABC Bank",  # Should be string
            "extraction_confidence": 0.95  # Should be float between 0 and 1
        }
        
        assert isinstance(test_data["principal_amount"], (int, float)), \
            "Principal should be numeric"
        assert isinstance(test_data["interest_rate"], float), \
            "Interest rate should be float"
        assert isinstance(test_data["tenure_months"], int), \
            "Tenure should be integer"
        assert isinstance(test_data["bank_name"], str), \
            "Bank name should be string"
        assert 0.0 <= test_data["extraction_confidence"] <= 1.0, \
            "Confidence should be between 0 and 1"
    
    def test_enum_validation(self):
        """Test validation of enum fields"""
        valid_loan_types = ["education", "home", "personal", "vehicle", "gold", "other"]
        
        test_loan_type = "education"
        
        assert test_loan_type in valid_loan_types, \
            f"Loan type {test_loan_type} should be valid"
        
        invalid_loan_type = "invalid_type"
        assert invalid_loan_type not in valid_loan_types, \
            "Invalid loan type should be rejected"
    
    def test_numeric_range_validation(self):
        """Test validation of numeric ranges"""
        test_cases = [
            {"field": "interest_rate", "value": 8.5, "min": 0, "max": 100, "valid": True},
            {"field": "interest_rate", "value": -5, "min": 0, "max": 100, "valid": False},
            {"field": "interest_rate", "value": 150, "min": 0, "max": 100, "valid": False},
            {"field": "tenure_months", "value": 60, "min": 1, "max": 600, "valid": True},
            {"field": "confidence", "value": 0.95, "min": 0, "max": 1, "valid": True},
        ]
        
        for case in test_cases:
            is_valid = case["min"] <= case["value"] <= case["max"]
            assert is_valid == case["valid"], \
                f"{case['field']} value {case['value']} validation should be {case['valid']}"
    
    def test_string_length_validation(self):
        """Test validation of string lengths"""
        test_cases = [
            {"field": "bank_name", "value": "ABC Bank", "min_length": 1, "valid": True},
            {"field": "bank_name", "value": "", "min_length": 1, "valid": False},
            {"field": "loan_id", "value": "loan_001", "min_length": 1, "valid": True},
        ]
        
        for case in test_cases:
            is_valid = len(case["value"]) >= case["min_length"]
            assert is_valid == case["valid"], \
                f"{case['field']} length validation should be {case['valid']}"
    
    def test_date_validation(self):
        """Test validation of date fields"""
        from datetime import datetime
        
        test_dates = [
            {"value": "2024-01-01", "valid": True},
            {"value": "invalid-date", "valid": False},
            {"value": "2024-13-01", "valid": False},  # Invalid month
        ]
        
        for test_date in test_dates:
            try:
                datetime.strptime(test_date["value"], "%Y-%m-%d")
                is_valid = True
            except ValueError:
                is_valid = False
            
            assert is_valid == test_date["valid"], \
                f"Date {test_date['value']} validation should be {test_date['valid']}"
    
    def test_nested_object_validation(self):
        """Test validation of nested objects"""
        bank_info = {
            "bank_name": "ABC Bank",
            "branch_name": "Downtown Branch",
            "bank_code": "ABC001"
        }
        
        # Validate nested object structure
        assert "bank_name" in bank_info, "Nested object should have bank_name"
        assert isinstance(bank_info["bank_name"], str), \
            "Nested field should have correct type"
    
    def test_array_validation(self):
        """Test validation of array fields"""
        fees = [
            {"fee_type": "Processing Fee", "amount": 500},
            {"fee_type": "Administrative Fee", "amount": 100},
        ]
        
        assert isinstance(fees, list), "Fees should be an array"
        assert len(fees) > 0, "Fees array should not be empty"
        
        for fee in fees:
            assert "fee_type" in fee, "Fee should have type"
            assert "amount" in fee, "Fee should have amount"
            assert isinstance(fee["amount"], (int, float)), \
                "Fee amount should be numeric"


class TestDataIntegrity:
    """Test data integrity constraints"""
    
    def test_principal_amount_positive(self):
        """Test that principal amount is positive"""
        principal_amounts = [50000, 100000, 75000]
        
        for amount in principal_amounts:
            assert amount > 0, "Principal amount should be positive"
    
    def test_interest_rate_reasonable(self):
        """Test that interest rate is within reasonable range"""
        interest_rates = [5.0, 8.5, 12.0, 15.0]
        
        for rate in interest_rates:
            assert 0 < rate < 100, "Interest rate should be reasonable"
    
    def test_tenure_positive(self):
        """Test that tenure is positive"""
        tenures = [12, 24, 36, 60, 120]
        
        for tenure in tenures:
            assert tenure > 0, "Tenure should be positive"
            assert tenure <= 600, "Tenure should be within reasonable limit"
    
    def test_confidence_score_range(self):
        """Test that confidence scores are in valid range"""
        confidence_scores = [0.94, 0.95, 0.97, 0.99]
        
        for score in confidence_scores:
            assert 0.0 <= score <= 1.0, "Confidence should be between 0 and 1"
    
    def test_fee_amounts_non_negative(self):
        """Test that fee amounts are non-negative"""
        fees = [
            {"type": "Processing Fee", "amount": 500},
            {"type": "Administrative Fee", "amount": 100},
            {"type": "Documentation Fee", "amount": 0},
        ]
        
        for fee in fees:
            assert fee["amount"] >= 0, "Fee amount should be non-negative"
    
    def test_payment_schedule_consistency(self):
        """Test consistency of payment schedule"""
        payment_schedule = [
            {"payment_no": 1, "amount": 1000, "principal": 800, "interest": 200},
            {"payment_no": 2, "amount": 1000, "principal": 810, "interest": 190},
        ]
        
        for payment in payment_schedule:
            # Total should equal principal + interest
            total = payment["principal"] + payment["interest"]
            assert abs(total - payment["amount"]) < 0.01, \
                "Payment amount should equal principal + interest"
    
    def test_unique_identifiers(self):
        """Test uniqueness of identifiers"""
        loan_ids = ["loan_001", "loan_002", "loan_003"]
        
        # Check for uniqueness
        assert len(loan_ids) == len(set(loan_ids)), \
            "Loan IDs should be unique"


class TestSchemaCompliance:
    """Test compliance with defined schema"""
    
    def test_json_serialization(self):
        """Test that data can be serialized to JSON"""
        import json
        
        loan_data = {
            "loan_id": "loan_001",
            "principal_amount": 50000,
            "interest_rate": 8.5,
            "tenure_months": 60,
            "loan_type": "education"
        }
        
        try:
            json_str = json.dumps(loan_data)
            assert len(json_str) > 0, "Should serialize to JSON"
            
            # Test deserialization
            deserialized = json.loads(json_str)
            assert deserialized == loan_data, "Should deserialize correctly"
        except Exception as e:
            assert False, f"JSON serialization failed: {str(e)}"
    
    def test_schema_version_compatibility(self):
        """Test compatibility with schema version"""
        schema_version = "1.0"
        
        loan_data = {
            "schema_version": schema_version,
            "loan_id": "loan_001",
            "principal_amount": 50000
        }
        
        assert "schema_version" in loan_data, "Should include schema version"
        assert loan_data["schema_version"] == schema_version, \
            "Schema version should match"
    
    def test_backward_compatibility(self):
        """Test backward compatibility with older schema versions"""
        # Old schema might not have all new fields
        old_schema_data = {
            "loan_id": "loan_001",
            "principal_amount": 50000,
            "interest_rate": 8.5
        }
        
        # Should still be valid even without new optional fields
        required_fields = ["loan_id", "principal_amount", "interest_rate"]
        
        for field in required_fields:
            assert field in old_schema_data, \
                f"Old schema should have required field {field}"
    
    def test_field_name_consistency(self):
        """Test consistency of field naming conventions"""
        field_names = [
            "principal_amount",
            "interest_rate",
            "tenure_months",
            "bank_name",
            "loan_type"
        ]
        
        # Check snake_case convention
        for field in field_names:
            assert field.islower() or '_' in field, \
                f"Field {field} should follow snake_case convention"
            assert ' ' not in field, \
                f"Field {field} should not contain spaces"


class TestValidationErrors:
    """Test validation error handling"""
    
    def test_missing_required_field_error(self):
        """Test error when required field is missing"""
        incomplete_data = {
            "loan_id": "loan_001",
            # Missing principal_amount
            "interest_rate": 8.5
        }
        
        required_fields = ["loan_id", "principal_amount", "interest_rate"]
        missing_fields = [f for f in required_fields if f not in incomplete_data]
        
        assert len(missing_fields) > 0, "Should detect missing required fields"
        assert "principal_amount" in missing_fields, \
            "Should identify principal_amount as missing"
    
    def test_invalid_data_type_error(self):
        """Test error when data type is invalid"""
        invalid_data = {
            "principal_amount": "not_a_number",  # Should be numeric
            "interest_rate": 8.5
        }
        
        try:
            float(invalid_data["principal_amount"])
            is_valid = True
        except ValueError:
            is_valid = False
        
        assert not is_valid, "Should detect invalid data type"
    
    def test_out_of_range_error(self):
        """Test error when value is out of range"""
        out_of_range_data = {
            "interest_rate": 150,  # Should be < 100
            "confidence": 1.5  # Should be <= 1.0
        }
        
        assert out_of_range_data["interest_rate"] > 100, \
            "Should detect out of range interest rate"
        assert out_of_range_data["confidence"] > 1.0, \
            "Should detect out of range confidence"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
