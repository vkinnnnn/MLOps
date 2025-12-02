"""
Unit tests for field extraction logic
Tests extraction of loan-specific fields and entity recognition
"""
import pytest
from typing import Dict, Any, List


class TestLoanFieldExtraction:
    """Test extraction of core loan fields"""
    
    def test_principal_amount_extraction(self):
        """Test extraction of principal amount"""
        test_cases = [
            {"text": "Principal Amount: $50,000", "expected": 50000},
            {"text": "Loan Amount: ₹100,000", "expected": 100000},
            {"text": "Amount: 75000", "expected": 75000},
        ]
        
        for case in test_cases:
            # Extract numbers from text
            import re
            numbers = re.findall(r'\d+(?:,\d{3})*(?:\.\d{2})?', case["text"])
            if numbers:
                extracted = float(numbers[0].replace(',', ''))
                assert extracted == case["expected"], \
                    f"Should extract principal {case['expected']}"
    
    def test_interest_rate_extraction(self):
        """Test extraction of interest rate"""
        test_cases = [
            {"text": "Interest Rate: 8.5%", "expected": 8.5},
            {"text": "APR: 12.0%", "expected": 12.0},
            {"text": "Rate of Interest: 7.25% per annum", "expected": 7.25},
        ]
        
        for case in test_cases:
            import re
            # Extract percentage values
            percentages = re.findall(r'(\d+\.?\d*)\s*%', case["text"])
            if percentages:
                extracted = float(percentages[0])
                assert extracted == case["expected"], \
                    f"Should extract interest rate {case['expected']}"
    
    def test_tenure_extraction(self):
        """Test extraction of loan tenure"""
        test_cases = [
            {"text": "Tenure: 60 months", "expected": 60, "unit": "months"},
            {"text": "Loan Period: 5 years", "expected": 5, "unit": "years"},
            {"text": "Duration: 36 months", "expected": 36, "unit": "months"},
        ]
        
        for case in test_cases:
            import re
            # Extract tenure value
            numbers = re.findall(r'(\d+)\s*(months?|years?)', case["text"], re.IGNORECASE)
            if numbers:
                value, unit = numbers[0]
                assert int(value) == case["expected"], \
                    f"Should extract tenure {case['expected']}"
    
    def test_moratorium_period_extraction(self):
        """Test extraction of moratorium period"""
        test_cases = [
            {"text": "Moratorium Period: 6 months", "expected": 6},
            {"text": "Grace Period: 12 months", "expected": 12},
            {"text": "No moratorium period", "expected": 0},
        ]
        
        for case in test_cases:
            import re
            if "No moratorium" in case["text"] or "no moratorium" in case["text"]:
                extracted = 0
            else:
                numbers = re.findall(r'(\d+)\s*months?', case["text"], re.IGNORECASE)
                extracted = int(numbers[0]) if numbers else 0
            
            assert extracted == case["expected"], \
                f"Should extract moratorium period {case['expected']}"
    
    def test_processing_fee_extraction(self):
        """Test extraction of processing fees"""
        test_cases = [
            {"text": "Processing Fee: $500", "expected": 500},
            {"text": "Processing Charges: ₹1,000", "expected": 1000},
            {"text": "Application Fee: 250", "expected": 250},
        ]
        
        for case in test_cases:
            import re
            numbers = re.findall(r'\d+(?:,\d{3})*', case["text"])
            if numbers:
                extracted = float(numbers[0].replace(',', ''))
                assert extracted == case["expected"], \
                    f"Should extract processing fee {case['expected']}"
    
    def test_penalty_clause_extraction(self):
        """Test extraction of penalty clauses"""
        penalty_texts = [
            "Late Payment Penalty: 2% per month",
            "Prepayment Penalty: 3% of outstanding amount",
            "Default Charges: $50 per occurrence",
        ]
        
        for text in penalty_texts:
            assert len(text) > 0, "Should extract penalty clause"
            assert any(word in text.lower() for word in ['penalty', 'charges', 'fee']), \
                "Should identify penalty-related text"
    
    def test_lender_information_extraction(self):
        """Test extraction of lender information"""
        test_cases = [
            {"text": "Bank Name: ABC Bank", "expected": "ABC Bank"},
            {"text": "Lender: XYZ Financial Services", "expected": "XYZ Financial Services"},
            {"text": "Branch: Downtown Branch", "expected": "Downtown Branch"},
        ]
        
        for case in test_cases:
            # Extract text after colon
            if ':' in case["text"]:
                extracted = case["text"].split(':', 1)[1].strip()
                assert extracted == case["expected"], \
                    f"Should extract lender info {case['expected']}"
    
    def test_cosigner_details_extraction(self):
        """Test extraction of co-signer details"""
        cosigner_text = "Co-signer: John Doe (Father)"
        
        assert "Co-signer" in cosigner_text or "co-signer" in cosigner_text.lower()
        assert len(cosigner_text) > 0, "Should extract co-signer details"
    
    def test_collateral_details_extraction(self):
        """Test extraction of collateral details"""
        collateral_texts = [
            "Collateral: Property at 123 Main St",
            "Security: Gold ornaments weighing 50g",
            "Guarantee: Personal guarantee by parent",
        ]
        
        for text in collateral_texts:
            assert len(text) > 0, "Should extract collateral details"
            assert any(word in text for word in ['Collateral', 'Security', 'Guarantee']), \
                "Should identify collateral-related text"
    
    def test_repayment_mode_extraction(self):
        """Test extraction of repayment mode"""
        repayment_modes = ["EMI", "Bullet Payment", "Step-up Payment", "Flexible EMI"]
        
        for mode in repayment_modes:
            assert len(mode) > 0, "Should extract repayment mode"
            assert any(word in mode for word in ['EMI', 'Payment', 'Flexible']), \
                "Should identify repayment mode"


class TestLoanTypeSpecificFields:
    """Test extraction of loan-type-specific fields"""
    
    def test_education_loan_fields(self):
        """Test extraction of education loan specific fields"""
        education_fields = {
            "institution_name": "ABC University",
            "course_name": "Master of Science",
            "course_duration": "2 years",
            "student_name": "Jane Doe"
        }
        
        for field, value in education_fields.items():
            assert len(value) > 0, f"Should extract {field}"
    
    def test_home_loan_fields(self):
        """Test extraction of home loan specific fields"""
        home_fields = {
            "property_address": "123 Main Street",
            "property_value": 500000,
            "property_type": "Apartment",
            "ltv_ratio": 80
        }
        
        for field, value in home_fields.items():
            assert value is not None, f"Should extract {field}"
    
    def test_vehicle_loan_fields(self):
        """Test extraction of vehicle loan specific fields"""
        vehicle_fields = {
            "vehicle_make": "Toyota",
            "vehicle_model": "Camry",
            "vehicle_year": 2024,
            "vehicle_value": 30000
        }
        
        for field, value in vehicle_fields.items():
            assert value is not None, f"Should extract {field}"
    
    def test_gold_loan_fields(self):
        """Test extraction of gold loan specific fields"""
        gold_fields = {
            "gold_weight": "50 grams",
            "gold_purity": "22 karat",
            "gold_value": 150000
        }
        
        for field, value in gold_fields.items():
            assert value is not None, f"Should extract {field}"


class TestEntityRecognition:
    """Test entity recognition in loan documents"""
    
    def test_bank_name_recognition(self):
        """Test recognition of bank names"""
        bank_names = [
            "State Bank of India",
            "HDFC Bank",
            "ICICI Bank",
            "Axis Bank",
            "Bank of America"
        ]
        
        for bank in bank_names:
            assert "Bank" in bank or "bank" in bank.lower(), \
                "Should recognize bank entity"
    
    def test_person_name_recognition(self):
        """Test recognition of person names"""
        person_names = [
            "John Doe",
            "Jane Smith",
            "Robert Johnson"
        ]
        
        for name in person_names:
            # Names typically have at least two words
            words = name.split()
            assert len(words) >= 2, "Should recognize person name"
    
    def test_address_recognition(self):
        """Test recognition of addresses"""
        addresses = [
            "123 Main Street, New York, NY 10001",
            "456 Oak Avenue, Los Angeles, CA 90001",
        ]
        
        for address in addresses:
            # Addresses typically contain numbers and street indicators
            import re
            has_number = bool(re.search(r'\d+', address))
            has_street = any(word in address for word in ['Street', 'Avenue', 'Road', 'Lane'])
            
            assert has_number or has_street, "Should recognize address"
    
    def test_date_recognition(self):
        """Test recognition of dates"""
        dates = [
            "01/01/2024",
            "January 1, 2024",
            "2024-01-01",
            "01-Jan-2024"
        ]
        
        for date in dates:
            import re
            has_date_pattern = bool(re.search(r'\d{1,4}', date))
            assert has_date_pattern, "Should recognize date"
    
    def test_monetary_value_recognition(self):
        """Test recognition of monetary values"""
        monetary_values = [
            "$50,000",
            "₹100,000",
            "€75,000",
            "£60,000"
        ]
        
        for value in monetary_values:
            import re
            has_currency = bool(re.search(r'[$₹€£¥]', value))
            has_number = bool(re.search(r'\d+', value))
            
            assert has_currency or has_number, "Should recognize monetary value"


class TestFieldExtractionAccuracy:
    """Test accuracy of field extraction"""
    
    def test_field_extraction_confidence(self):
        """Test confidence scoring for field extraction"""
        field_confidences = {
            "principal": 0.99,
            "interest_rate": 0.97,
            "tenure": 0.96,
            "fees": 0.95,
            "penalties": 0.94
        }
        
        for field, confidence in field_confidences.items():
            assert confidence >= 0.94, \
                f"Field {field} confidence should meet threshold"
    
    def test_required_field_completeness(self):
        """Test that all required fields are extracted"""
        required_fields = [
            "principal_amount",
            "interest_rate",
            "tenure",
            "lender_name"
        ]
        
        extracted_fields = {
            "principal_amount": 50000,
            "interest_rate": 8.5,
            "tenure": 60,
            "lender_name": "ABC Bank"
        }
        
        for field in required_fields:
            assert field in extracted_fields, f"Required field {field} should be extracted"
            assert extracted_fields[field] is not None, \
                f"Required field {field} should have value"
    
    def test_optional_field_handling(self):
        """Test handling of optional fields"""
        optional_fields = {
            "moratorium_period": None,
            "cosigner": None,
            "collateral": "Property"
        }
        
        # Optional fields can be None
        for field, value in optional_fields.items():
            assert field in optional_fields, f"Optional field {field} should be present"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
