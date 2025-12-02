"""
Simple test runner that doesn't require pytest
Runs all test modules and generates a summary report
"""
import sys
import os
import importlib.util
import traceback

# Add Lab3 to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_test_module(module_path):
    """Run a single test module"""
    module_name = os.path.basename(module_path).replace('.py', '')
    
    print(f"\n{'='*80}")
    print(f"Running: {module_name}")
    print('='*80)
    
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find all test classes
        test_classes = []
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and name.startswith('Test'):
                test_classes.append(obj)
        
        # Run tests in each class
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for test_class in test_classes:
            print(f"\n{test_class.__name__}:")
            
            # Find all test methods
            test_methods = [m for m in dir(test_class) if m.startswith('test_')]
            
            for method_name in test_methods:
                total_tests += 1
                try:
                    # Create instance and run test
                    instance = test_class()
                    method = getattr(instance, method_name)
                    method()
                    
                    print(f"  ✓ {method_name}")
                    passed_tests += 1
                    
                except AssertionError as e:
                    print(f"  ✗ {method_name}")
                    print(f"    AssertionError: {str(e)}")
                    failed_tests += 1
                    
                except Exception as e:
                    print(f"  ✗ {method_name}")
                    print(f"    Error: {str(e)}")
                    failed_tests += 1
        
        return total_tests, passed_tests, failed_tests
        
    except Exception as e:
        print(f"✗ Failed to load module: {str(e)}")
        traceback.print_exc()
        return 0, 0, 1


def run_all_tests():
    """Run all unit tests and generate report"""
    print("=" * 80)
    print("Running Unit Tests for Loan Document Extractor Platform")
    print("=" * 80)
    
    # Get the tests directory
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Test modules to run
    test_files = [
        "test_document_validation.py",
        "test_ocr_extraction.py",
        "test_table_extraction.py",
        "test_field_extraction.py",
        "test_data_normalization.py",
        "test_schema_validation.py",
        "test_metrics_calculation.py",
    ]
    
    total_all = 0
    passed_all = 0
    failed_all = 0
    
    for test_file in test_files:
        test_path = os.path.join(tests_dir, test_file)
        if os.path.exists(test_path):
            total, passed, failed = run_test_module(test_path)
            total_all += total
            passed_all += passed
            failed_all += failed
        else:
            print(f"\n✗ Test file not found: {test_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests:  {total_all}")
    print(f"Passed:       {passed_all} ({passed_all/total_all*100:.1f}%)" if total_all > 0 else "Passed:       0")
    print(f"Failed:       {failed_all} ({failed_all/total_all*100:.1f}%)" if total_all > 0 else "Failed:       0")
    print("=" * 80)
    
    if failed_all == 0 and total_all > 0:
        print("✓ All tests passed successfully!")
        return 0
    else:
        print("✗ Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
