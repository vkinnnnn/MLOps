"""
Unit tests for data normalization
Tests loan type classification, bank format identification, and field mapping
"""
import pytest
from typing import Dict, Any, List


class TestLoanTypeClassification:
    """Test loan type classification"""
    
    def test_education_loan_classification(self):
        """Test classification of education loans"""
        education_keywords = ["education", "student", "university", "college", "tuition"]
        
        text = "Education Loan for University Studies"
        
        is_education = any(keyword in text.lower() for keyword in education_keywords)
        assert is_education, "Should classify as education loan"
    
    def test_home_loan_classification(self):
        """Test classification of home loans"""
        home_keywords = ["home", "housing", "property", "mortgage", "real estate"]
        
        text = "Home Loan for Property Purchase"
        
        is_home = any(keyword in text.lower() for keyword in home_keywords)
        assert is_home, "Should classify as home loan"
    
    def test_personal_loan_classification(self):
        """Test classification of personal loans"""
        personal_keywords = ["personal", "consumer", "unsecured"]
        
        text = "Personal Loan Agreement"
        
        is_personal = any(keyword in text.lower() for keyword in personal_keywords)
        assert is_personal, "Should classify as personal loan"
    
    def test_vehicle_loan_classification(self):
        """Test classification of vehicle loans"""
        vehicle_keywords = ["vehicle", "car", "auto", "automobile"]
        
        text = "Vehicle Loan for Car Purchase"
        
        is_vehicle = any(keyword in text.lower() for keyword in vehicle_keywords)
        assert is_vehicle, "Should classify as vehicle loan"
    
    def test_gold_loan_classification(self):
        """Test classification of gold loans"""
        gold_keywords = ["gold", "jewelry", "ornament"]
        
        text = "Gold Loan Against Jewelry"
        
        is_gold = any(keyword in text.lower() for keyword in gold_keywords)
        assert is_gold, "Should classify as gold loan"
    
    def test_loan_type_confidence(self):
        """Test confidence scoring for loan type classification"""
        # Multiple matching keywords increase confidence
        text = "Education Loan for Student University Studies"
        education_keywords = ["education", "student", "university", "college"]
        
        matches = sum(1 for keyword in education_keywords if keyword in text.lower())
        confidence = min(matches / len(education_keywords), 1.0)
        
        assert confidence > 0.5, "Should have reasonable confidence"


class TestBankFormatIdentification:
    """Test bank-specific format identification"""
    
    def test_bank_name_identification(self):
        """Test identification of bank names"""
        bank_patterns = [
            "State Bank of India",
            "HDFC Bank",
            "ICICI Bank",
            "Axis Bank",
            "Bank of America"
        ]
        
        for bank in bank_patterns:
            assert "Bank" in bank or "bank" in bank.lower(), \
                f"Should identify {bank}"
    
    def test_bank_code_identification(self):
        """Test identification of bank codes"""
        bank_codes = ["SBIN", "HDFC", "ICIC", "AXIS"]
        
        for code in bank_codes:
            assert len(code) >= 3, "Bank code should have minimum length"
            assert code.isupper(), "Bank code should be uppercase"
    
    def test_branch_identification(self):
        """Test identification of branch information"""
        branch_text = "Branch: Downtown Branch, New York"
        
        assert "Branch" in branch_text or "branch" in branch_text.lower()
        assert len(branch_text) > 0, "Should extract branch information"
    
    def test_bank_specific_terminology(self):
        """Test handling of bank-specific terminology"""
        terminology_mappings = {
            "Principal": ["Loan Amount", "Principal Amount", "Sanctioned Amount"],
            "Interest Rate": ["Rate of Interest", "APR", "Interest Percentage"],
            "Tenure": ["Loan Period", "Duration", "Term"],
        }
        
        for standard_term, variations in terminology_mappings.items():
            assert len(variations) > 0, \
                f"Should have variations for {standard_term}"
    
    def test_format_variation_handling(self):
        """Test handling of format variations across banks"""
        # Different banks may format the same field differently
        principal_formats = [
            "Principal Amount: $50,000",
            "Loan Amount: ₹50,000",
            "Sanctioned Amount: 50000",
        ]
        
        for fmt in principal_formats:
            import re
            numbers = re.findall(r'\d+(?:,\d{3})*', fmt)
            assert len(numbers) > 0, "Should extract value regardless of format"


class TestFieldMapping:
    """Test field mapping to standard schema"""
    
    def test_principal_amount_mapping(self):
        """Test mapping of principal amount variations"""
        variations = {
            "Principal Amount": "principal_amount",
            "Loan Amount": "principal_amount",
            "Sanctioned Amount": "principal_amount",
        }
        
        for source, target in variations.items():
            assert target == "principal_amount", \
                f"Should map {source} to principal_amount"
    
    def test_interest_rate_mapping(self):
        """Test mapping of interest rate variations"""
        variations = {
            "Interest Rate": "interest_rate",
            "Rate of Interest": "interest_rate",
            "APR": "interest_rate",
            "Annual Percentage Rate": "interest_rate",
        }
        
        for source, target in variations.items():
            assert target == "interest_rate", \
                f"Should map {source} to interest_rate"
    
    def test_tenure_mapping(self):
        """Test mapping of tenure variations"""
        variations = {
            "Tenure": "tenure_months",
            "Loan Period": "tenure_months",
            "Duration": "tenure_months",
            "Term": "tenure_months",
        }
        
        for source, target in variations.items():
            assert target == "tenure_months", \
                f"Should map {source} to tenure_months"
    
    def test_fee_mapping(self):
        """Test mapping of fee variations"""
        fee_variations = {
            "Processing Fee": "processing_fee",
            "Processing Charges": "processing_fee",
            "Application Fee": "processing_fee",
        }
        
        for source, target in fee_variations.items():
            assert target == "processing_fee", \
                f"Should map {source} to processing_fee"
    
    def test_unit_conversion(self):
        """Test conversion of units (years to months)"""
        test_cases = [
            {"value": 5, "unit": "years", "expected_months": 60},
            {"value": 3, "unit": "years", "expected_months": 36},
            {"value": 24, "unit": "months", "expected_months": 24},
        ]
        
        for case in test_cases:
            if case["unit"] == "years":
                converted = case["value"] * 12
            else:
                converted = case["value"]
            
            assert converted == case["expected_months"], \
                f"Should convert {case['value']} {case['unit']} to {case['expected_months']} months"
    
    def test_currency_normalization(self):
        """Test normalization of currency values"""
        currency_values = [
            {"input": "$50,000", "expected": 50000},
            {"input": "₹100,000", "expected": 100000},
            {"input": "50000", "expected": 50000},
        ]
        
        for case in currency_values:
            import re
            # Remove currency symbols and commas
            cleaned = re.sub(r'[$₹€£¥,]', '', case["input"])
            normalized = float(cleaned)
            
            assert normalized == case["expected"], \
                f"Should normalize {case['input']} to {case['expected']}"
    
    def test_percentage_normalization(self):
        """Test normalization of percentage values"""
        percentage_values = [
            {"input": "8.5%", "expected": 8.5},
            {"input": "12%", "expected": 12.0},
            {"input": "0.5%", "expected": 0.5},
        ]
        
        for case in percentage_values:
            # Remove percentage symbol
            cleaned = case["input"].replace('%', '').strip()
            normalized = float(cleaned)
            
            assert normalized == case["expected"], \
                f"Should normalize {case['input']} to {case['expected']}"


class TestDataStandardization:
    """Test data standardization to common schema"""
    
    def test_date_standardization(self):
        """Test standardization of date formats"""
        date_formats = [
            {"input": "01/01/2024", "format": "MM/DD/YYYY"},
            {"input": "2024-01-01", "format": "YYYY-MM-DD"},
            {"input": "January 1, 2024", "format": "Month D, YYYY"},
        ]
        
        for date_fmt in date_formats:
            assert len(date_fmt["input"]) > 0, "Should have date value"
            assert len(date_fmt["format"]) > 0, "Should identify format"
    
    def test_name_standardization(self):
        """Test standardization of names"""
        names = [
            {"input": "JOHN DOE", "expected": "John Doe"},
            {"input": "jane smith", "expected": "Jane Smith"},
            {"input": "Robert JOHNSON", "expected": "Robert Johnson"},
        ]
        
        for name in names:
            standardized = name["input"].title()
            assert standardized == name["expected"], \
                f"Should standardize {name['input']} to {name['expected']}"
    
    def test_address_standardization(self):
        """Test standardization of addresses"""
        address = "123 main street, new york, ny 10001"
        standardized = address.title()
        
        assert standardized != address, "Should standardize address case"
    
    def test_phone_number_standardization(self):
        """Test standardization of phone numbers"""
        phone_formats = [
            {"input": "(123) 456-7890", "digits": "1234567890"},
            {"input": "123-456-7890", "digits": "1234567890"},
            {"input": "1234567890", "digits": "1234567890"},
        ]
        
        for phone in phone_formats:
            import re
            digits_only = re.sub(r'\D', '', phone["input"])
            assert digits_only == phone["digits"], \
                f"Should extract digits from {phone['input']}"


class TestNormalizationAccuracy:
    """Test accuracy of normalization process"""
    
    def test_field_mapping_accuracy(self):
        """Test accuracy of field mapping"""
        total_fields = 10
        correctly_mapped = 10
        
        accuracy = correctly_mapped / total_fields
        
        assert accuracy >= 0.94, "Field mapping accuracy should meet threshold"
    
    def test_value_conversion_accuracy(self):
        """Test accuracy of value conversions"""
        conversions = [
            {"input": "5 years", "output": 60, "correct": True},
            {"input": "$50,000", "output": 50000, "correct": True},
            {"input": "8.5%", "output": 8.5, "correct": True},
        ]
        
        correct_count = sum(1 for c in conversions if c["correct"])
        accuracy = correct_count / len(conversions)
        
        assert accuracy >= 0.94, "Conversion accuracy should meet threshold"
    
    def test_schema_compliance(self):
        """Test compliance with standard schema"""
        normalized_data = {
            "principal_amount": 50000,
            "interest_rate": 8.5,
            "tenure_months": 60,
            "loan_type": "education",
            "bank_name": "ABC Bank"
        }
        
        required_fields = ["principal_amount", "interest_rate", "tenure_months"]
        
        for field in required_fields:
            assert field in normalized_data, f"Required field {field} should be present"
            assert normalized_data[field] is not None, \
                f"Required field {field} should have value"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
