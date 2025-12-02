"""
Test runner for all unit tests
Runs all test modules and generates a summary report
"""
import sys
import os

# Add Lab3 to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


def run_all_tests():
    """Run all unit tests and generate report"""
    print("=" * 80)
    print("Running Unit Tests for Loan Document Extractor Platform")
    print("=" * 80)
    print()
    
    # Test modules to run
    test_modules = [
        "tests/test_document_validation.py",
        "tests/test_ocr_extraction.py",
        "tests/test_table_extraction.py",
        "tests/test_field_extraction.py",
        "tests/test_data_normalization.py",
        "tests/test_schema_validation.py",
        "tests/test_metrics_calculation.py",
    ]
    
    # Run tests with verbose output
    args = [
        "-v",  # Verbose
        "--tb=short",  # Short traceback format
        "--color=yes",  # Colored output
    ] + test_modules
    
    exit_code = pytest.main(args)
    
    print()
    print("=" * 80)
    if exit_code == 0:
        print("✓ All tests passed successfully!")
    else:
        print("✗ Some tests failed. Please review the output above.")
    print("=" * 80)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(run_all_tests())
