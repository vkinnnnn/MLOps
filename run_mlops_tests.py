"""Test runner for MLOps pipeline modules.

This script runs all MLOps unit tests and generates coverage reports.
"""

import sys
import subprocess
from pathlib import Path


def run_tests():
    """Run all MLOps tests with coverage."""
    
    print("=" * 70)
    print("Running MLOps Pipeline Tests")
    print("=" * 70)
    print()
    
    # Test files
    test_files = [
        "tests/test_mlops_data_acquisition.py",
        "tests/test_mlops_validation.py",
        "tests/test_mlops_anomaly_detection.py",
        "tests/test_mlops_bias_detection.py"
    ]
    
    # Run pytest with coverage
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        "--cov=mlops",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        *test_files
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    print()
    print("=" * 70)
    if result.returncode == 0:
        print("✅ All tests passed!")
        print("Coverage report saved to: htmlcov/index.html")
    else:
        print("❌ Some tests failed")
    print("=" * 70)
    
    return result.returncode


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
