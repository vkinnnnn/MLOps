# Quick Start Guide - Unit Tests

## Running Tests in 30 Seconds

### Step 1: Run verification (fastest) from the project root
```bash
python tests/verify_tests.py
```

This will run one test from each module to verify everything works.

### Step 3: Run full test suite

**Option A - With pytest** (recommended):
```bash
pip install pytest
pytest tests/ -v
```

**Option B - Without pytest**:
```bash
python tests/run_tests_simple.py
```

## What Gets Tested

 Document validation (PDF, JPEG, PNG, TIFF)
 OCR extraction accuracy (94% threshold)
 Table detection and extraction
 Field extraction (principal, rate, tenure, etc.)
 Data normalization (loan types, bank formats)
 Schema validation (Pydantic models)
 Metrics calculation (cost, EMI, flexibility)

## Test Results

You should see output like:

```
================================================================================
Running Unit Tests for Loan Document Extractor Platform
================================================================================

TestDocumentValidation:
 test_pdf_format_validation
 test_jpeg_format_validation
 test_png_format_validation
 ...

================================================================================
TEST SUMMARY
================================================================================
Total Tests: 132
Passed: 132 (100.0%)
Failed: 0 (0.0%)
================================================================================
 All tests passed successfully!
```

## Troubleshooting

### "Python was not found"
- Install Python 3.10+ (or compatible) from python.org
- Add Python to PATH during installation
- Or use: `C:\Path\To\Python\python.exe tests/verify_tests.py`

### "No module named pytest"
- Use the simple runner: `python tests/run_tests_simple.py`
- Or install pytest: `pip install pytest`

### Import errors
- Make sure you're in the project root directory
- Check that `__init__.py` exists in tests folder

## Individual Test Modules

Run specific test modules:

```bash
python tests/test_document_validation.py
python tests/test_ocr_extraction.py
python tests/test_table_extraction.py
python tests/test_field_extraction.py
python tests/test_data_normalization.py
python tests/test_schema_validation.py
python tests/test_metrics_calculation.py
```

## Test Coverage Summary

| Module | Tests | Coverage |
|--------|-------|----------|
| Document Validation | 12 | Format validation, file handling |
| OCR Extraction | 15 | Text extraction, accuracy metrics |
| Table Extraction | 20 | Tables, payment schedules, fees |
| Field Extraction | 20 | Loan fields, entity recognition |
| Data Normalization | 20 | Classification, mapping, conversion |
| Schema Validation | 20 | Data types, constraints, integrity |
| Metrics Calculation | 25 | Cost, EMI, flexibility, comparison |
| **TOTAL** | **132** | **All core functionality** |

## Need More Info?

- Full documentation: `tests/README.md`
- Implementation details: `tests/TEST_IMPLEMENTATION_SUMMARY.md`
- Requirements: `.kiro/specs/loan-document-explainer/requirements.md`
- Design: `.kiro/specs/loan-document-explainer/design.md`

## Success Criteria

 All 132 tests pass
 No syntax errors
 94% accuracy threshold validated
 All requirements covered
 Ready for CI/CD integration

---

**Status**: Task 17.1 Complete - All unit tests implemented and verified
