# Unit Tests for Loan Document Extractor Platform

This directory contains comprehensive unit tests for the Student Loan Document Extractor Platform, covering all core functionality as specified in the requirements and design documents.

## Test Coverage

### 1. Document Validation Tests (`test_document_validation.py`)
- PDF, JPEG, PNG, TIFF format validation
- File size validation
- MIME type detection
- Empty and corrupted file detection
- Multi-page document handling
- Page limit enforcement (50 pages)

### 2. OCR Extraction Tests (`test_ocr_extraction.py`)
- Text extraction confidence scoring
- Number and currency extraction
- Percentage and date extraction
- Multi-line text handling
- Special character preservation
- Handwritten text confidence
- Mixed content extraction
- 94% accuracy threshold validation
- F1 score calculation

### 3. Table Extraction Tests (`test_table_extraction.py`)
- Simple table detection
- Payment schedule table detection
- Fee structure table detection
- Nested column detection and preservation
- Multi-page table handling
- Header and row data extraction
- Merged cell handling
- Table structure preservation
- Cell extraction accuracy

### 4. Field Extraction Tests (`test_field_extraction.py`)
- Principal amount extraction
- Interest rate extraction
- Tenure extraction
- Moratorium period extraction
- Processing fee extraction
- Penalty clause extraction
- Lender information extraction
- Co-signer details extraction
- Collateral details extraction
- Repayment mode extraction
- Loan-type-specific fields (education, home, vehicle, gold)
- Entity recognition (bank names, person names, addresses, dates)

### 5. Data Normalization Tests (`test_data_normalization.py`)
- Loan type classification (education, home, personal, vehicle, gold)
- Bank format identification
- Bank-specific terminology mapping
- Field mapping to standard schema
- Unit conversion (years to months)
- Currency normalization
- Percentage normalization
- Date standardization
- Name and address standardization

### 6. Schema Validation Tests (`test_schema_validation.py`)
- Required field validation
- Optional field validation
- Data type validation
- Enum validation
- Numeric range validation
- String length validation
- Date validation
- Nested object validation
- Array validation
- Data integrity constraints
- JSON serialization
- Schema version compatibility

### 7. Metrics Calculation Tests (`test_metrics_calculation.py`)
- Total cost calculation (with interest and fees)
- Effective interest rate calculation
- APR calculation
- Flexibility score calculation
- Monthly EMI calculation
- Comparison metrics (cost, flexibility, rate)
- Multi-criteria comparison
- Pros and cons generation
- Calculation precision and rounding

## Running the Tests

### Option 1: Using pytest (Recommended)

If pytest is installed:

```bash
# Run all tests
pytest tests/ -v

# Run specific test module
pytest tests/test_document_validation.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Option 2: Using the simple test runner

If pytest is not available, use the simple test runner from the project root:

```bash
python tests/run_tests_simple.py
```

### Option 3: Run individual test modules

Each test module can be run independently:

```bash
python tests/test_document_validation.py
python tests/test_ocr_extraction.py
python tests/test_table_extraction.py
# ... etc
```

## Test Requirements

These tests validate that the system meets all requirements specified in:
- `.kiro/specs/loan-document-explainer/requirements.md`
- `.kiro/specs/loan-document-explainer/design.md`

Key requirements validated:
- **Requirement 2.13**: 94% extraction accuracy (F1 score)
- **Requirement 3**: OCR processing for printed, scanned, and handwritten text
- **Requirement 3A**: Complex layout and table processing
- **Requirement 3B**: Multi-page document processing (up to 50 pages)
- **Requirement 3C**: Diverse loan type support
- **Requirement 3D**: Bank-specific format handling
- **Requirement 4**: Structured data output
- **Requirement 5**: Comparison metrics calculation

## Test Structure

Each test module follows this structure:

```python
class TestFeatureName:
 """Test specific feature"""
 
 def test_specific_functionality(self):
 """Test description"""
 # Arrange
 test_data = {...}
 
 # Act
 result = function_under_test(test_data)
 
 # Assert
 assert result == expected_value
```

## Notes

- Tests are designed to be **minimal** and focus on **core functionality**
- Tests validate **logic and algorithms** rather than external dependencies
- Tests use **mock data** to avoid requiring actual Document AI or database connections
- All tests follow the **AAA pattern** (Arrange, Act, Assert)
- Tests are **independent** and can run in any order

## Adding New Tests

When adding new tests:

1. Create a new test file: `test_<feature_name>.py`
2. Import pytest: `import pytest`
3. Create test classes: `class TestFeatureName:`
4. Add test methods: `def test_specific_case(self):`
5. Use descriptive names and docstrings
6. Follow the existing test structure
7. Update this README with the new test coverage

## Continuous Integration

These tests are designed to be run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
 run: |
 pip install pytest
 pytest tests/ -v --tb=short
```

## Test Data

Test data is embedded in the test files to ensure tests are:
- **Self-contained**: No external dependencies
- **Reproducible**: Same results every time
- **Fast**: No I/O operations
- **Reliable**: No network calls or external services

## Coverage Goals

Target test coverage:
- **Unit tests**: 80%+ code coverage
- **Critical paths**: 100% coverage
- **Edge cases**: Comprehensive coverage
- **Error handling**: All error paths tested

## Troubleshooting

### Python not found
If you get "Python was not found" error:
1. Ensure Python 3.10+ is installed
2. Add Python to your PATH
3. Use the full path to Python executable
4. Check if you're in a virtual environment

### Import errors
If you get import errors:
1. Ensure you're running from the project root directory
2. Check that `__init__.py` files exist
3. Verify PYTHONPATH includes the project root

### Test failures
If tests fail:
1. Check the error message and traceback
2. Verify test data matches expected format
3. Ensure all dependencies are installed
4. Check for environment-specific issues

## Contact

For questions or issues with tests, refer to:
- Requirements: `.kiro/specs/loan-document-explainer/requirements.md`
- Design: `.kiro/specs/loan-document-explainer/design.md`
- Tasks: `.kiro/specs/loan-document-explainer/tasks.md`
