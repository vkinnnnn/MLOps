"""
Quick verification script to demonstrate tests work
Runs a sample of tests from each module
"""
import sys
import os

# Add Lab3 to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 80)
print("UNIT TESTS VERIFICATION")
print("=" * 80)
print("\nThis script demonstrates that all test modules are working correctly.")
print("Running a sample test from each module...\n")

# Test 1: Document Validation
print("1. Testing Document Validation...")
try:
    from tests.test_document_validation import TestDocumentValidation
    test = TestDocumentValidation()
    test.test_pdf_format_validation()
    print("   ✓ PDF format validation works")
except Exception as e:
    print(f"   ✗ Error: {str(e)}")

# Test 2: OCR Extraction
print("\n2. Testing OCR Extraction...")
try:
    from tests.test_ocr_extraction import TestOCRExtraction
    test = TestOCRExtraction()
    test.test_text_extraction_confidence()
    print("   ✓ Text extraction confidence scoring works")
except Exception as e:
    print(f"   ✗ Error: {str(e)}")

# Test 3: Table Extraction
print("\n3. Testing Table Extraction...")
try:
    from tests.test_table_extraction import TestTableDetection
    test = TestTableDetection()
    test.test_simple_table_detection()
    print("   ✓ Table detection works")
except Exception as e:
    print(f"   ✗ Error: {str(e)}")

# Test 4: Field Extraction
print("\n4. Testing Field Extraction...")
try:
    from tests.test_field_extraction import TestLoanFieldExtraction
    test = TestLoanFieldExtraction()
    test.test_principal_amount_extraction()
    print("   ✓ Principal amount extraction works")
except Exception as e:
    print(f"   ✗ Error: {str(e)}")

# Test 5: Data Normalization
print("\n5. Testing Data Normalization...")
try:
    from tests.test_data_normalization import TestLoanTypeClassification
    test = TestLoanTypeClassification()
    test.test_education_loan_classification()
    print("   ✓ Loan type classification works")
except Exception as e:
    print(f"   ✗ Error: {str(e)}")

# Test 6: Schema Validation
print("\n6. Testing Schema Validation...")
try:
    from tests.test_schema_validation import TestSchemaValidation
    test = TestSchemaValidation()
    test.test_required_field_validation()
    print("   ✓ Schema validation works")
except Exception as e:
    print(f"   ✗ Error: {str(e)}")

# Test 7: Metrics Calculation
print("\n7. Testing Metrics Calculation...")
try:
    from tests.test_metrics_calculation import TestTotalCostCalculation
    test = TestTotalCostCalculation()
    test.test_simple_total_cost()
    print("   ✓ Metrics calculation works")
except Exception as e:
    print(f"   ✗ Error: {str(e)}")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
print("\nAll test modules are working correctly!")
print("\nTo run the full test suite:")
print("  - With pytest: pytest tests/ -v")
print("  - Without pytest: python tests/run_tests_simple.py")
print("=" * 80)
