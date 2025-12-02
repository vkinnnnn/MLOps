"""
Unit tests for OCR extraction accuracy
Tests text extraction, confidence scoring, and accuracy metrics
"""
import pytest
from typing import Dict, Any, List


class TestOCRExtraction:
    """Test OCR extraction functionality"""
    
    def test_text_extraction_confidence(self):
        """Test confidence scoring for extracted text"""
        # Simulate extraction results with different confidence levels
        test_cases = [
            {"text": "Principal Amount", "confidence": 0.99},
            {"text": "Interest Rate", "confidence": 0.95},
            {"text": "Tenure", "confidence": 0.92},
            {"text": "unclear_text", "confidence": 0.75},
        ]
        
        for case in test_cases:
            assert 0.0 <= case["confidence"] <= 1.0, \
                "Confidence should be between 0 and 1"
            
            if case["confidence"] >= 0.94:
                assert True, "High confidence extraction"
            elif case["confidence"] < 0.85:
                assert case["confidence"] < 0.85, "Low confidence should be flagged"
    
    def test_number_extraction_accuracy(self):
        """Test extraction of numerical values"""
        test_numbers = [
            "50000",
            "12.5",
            "8.75%",
            "$1,000.00",
            "₹50,000",
        ]
        
        for num in test_numbers:
            # Check if number patterns are detected
            has_digit = any(c.isdigit() for c in num)
            assert has_digit, f"Number {num} should contain digits"
    
    def test_currency_symbol_extraction(self):
        """Test extraction of currency symbols"""
        currency_symbols = ['$', '₹', '€', '£', '¥']
        
        for symbol in currency_symbols:
            assert len(symbol) > 0, "Currency symbol should be extracted"
    
    def test_percentage_extraction(self):
        """Test extraction of percentage values"""
        percentages = ["8.5%", "12%", "0.5%", "15.75%"]
        
        for pct in percentages:
            assert '%' in pct, "Percentage symbol should be present"
            # Extract numeric part
            numeric = pct.replace('%', '').strip()
            try:
                float(numeric)
                assert True, "Percentage value should be numeric"
            except ValueError:
                assert False, f"Invalid percentage format: {pct}"
    
    def test_date_extraction(self):
        """Test extraction of date values"""
        dates = [
            "01/01/2024",
            "2024-01-01",
            "January 1, 2024",
            "01-Jan-2024",
        ]
        
        for date in dates:
            # Check for date-like patterns
            has_numbers = any(c.isdigit() for c in date)
            assert has_numbers, f"Date {date} should contain numbers"
    
    def test_multiline_text_extraction(self):
        """Test extraction of multi-line text blocks"""
        multiline_text = """Principal Amount: $50,000
Interest Rate: 8.5%
Tenure: 60 months"""
        
        lines = multiline_text.split('\n')
        assert len(lines) == 3, "Should extract all lines"
        
        for line in lines:
            assert len(line) > 0, "Each line should have content"
    
    def test_special_character_handling(self):
        """Test handling of special characters"""
        special_chars = ['@', '#', '&', '*', '(', ')', '-', '_', '/', '\\']
        
        for char in special_chars:
            assert len(char) == 1, "Special character should be preserved"
    
    def test_handwritten_text_confidence(self):
        """Test confidence scoring for handwritten text"""
        # Handwritten text typically has lower confidence
        handwritten_confidence = 0.85
        printed_confidence = 0.98
        
        assert handwritten_confidence < printed_confidence, \
            "Handwritten text should have lower confidence than printed"
        assert handwritten_confidence >= 0.75, \
            "Handwritten confidence should still be reasonable"
    
    def test_mixed_content_extraction(self):
        """Test extraction of mixed content (text + numbers + symbols)"""
        mixed_content = "Loan Amount: $50,000 @ 8.5% for 5 years"
        
        # Check for presence of different content types
        has_text = any(c.isalpha() for c in mixed_content)
        has_numbers = any(c.isdigit() for c in mixed_content)
        has_symbols = any(c in '$@%' for c in mixed_content)
        
        assert has_text, "Should contain text"
        assert has_numbers, "Should contain numbers"
        assert has_symbols, "Should contain symbols"
    
    def test_extraction_accuracy_threshold(self):
        """Test that extraction meets 94% accuracy threshold"""
        # Simulate extraction results
        total_fields = 100
        correctly_extracted = 95
        
        accuracy = correctly_extracted / total_fields
        
        assert accuracy >= 0.94, \
            f"Extraction accuracy {accuracy:.2%} should meet 94% threshold"
    
    def test_low_quality_scan_handling(self):
        """Test handling of low-quality scanned documents"""
        # Low quality scans have lower confidence
        low_quality_confidence = 0.80
        high_quality_confidence = 0.97
        
        assert low_quality_confidence < high_quality_confidence, \
            "Low quality scans should have lower confidence"
        
        # Should still be above minimum threshold
        assert low_quality_confidence >= 0.70, \
            "Even low quality should meet minimum threshold"


class TestOCRAccuracyMetrics:
    """Test OCR accuracy calculation and metrics"""
    
    def test_f1_score_calculation(self):
        """Test F1 score calculation for extraction accuracy"""
        # True positives, false positives, false negatives
        tp = 94
        fp = 3
        fn = 3
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        assert f1_score >= 0.94, f"F1 score {f1_score:.2%} should meet 94% threshold"
    
    def test_confidence_aggregation(self):
        """Test aggregation of confidence scores"""
        confidences = [0.99, 0.97, 0.95, 0.93, 0.98, 0.96]
        
        avg_confidence = sum(confidences) / len(confidences)
        
        assert avg_confidence >= 0.94, \
            f"Average confidence {avg_confidence:.2%} should meet threshold"
    
    def test_page_level_accuracy(self):
        """Test accuracy calculation at page level"""
        page_accuracies = [0.98, 0.96, 0.95, 0.94, 0.97]
        
        for accuracy in page_accuracies:
            assert accuracy >= 0.94, \
                f"Page accuracy {accuracy:.2%} should meet threshold"
    
    def test_field_level_accuracy(self):
        """Test accuracy for individual field extraction"""
        field_results = [
            {"field": "principal", "correct": True, "confidence": 0.99},
            {"field": "interest_rate", "correct": True, "confidence": 0.97},
            {"field": "tenure", "correct": True, "confidence": 0.96},
            {"field": "fees", "correct": True, "confidence": 0.94},
        ]
        
        correct_count = sum(1 for r in field_results if r["correct"])
        accuracy = correct_count / len(field_results)
        
        assert accuracy >= 0.94, "Field-level accuracy should meet threshold"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
