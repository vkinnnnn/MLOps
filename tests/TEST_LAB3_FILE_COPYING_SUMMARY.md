# Lab3 File Copying Property-Based Tests - Summary

## Overview

This document summarizes the property-based tests implemented for validating file copying operations during the Lab3-LoanQA integration process.

## Test File

**Location:** `tests/test_lab3_file_copying.py`

## Property Tested

**Property 1: File copying preserves all source files**

*For any* source directory and destination directory in the Lab3 component migration, after copying, every file that exists in the source directory should have a corresponding file in the destination directory with the same relative path and content.

**Validates:** Requirements 2.2, 2.3, 2.4, 2.5, 2.6

## Test Implementation

### Property-Based Tests (using Hypothesis)

1. **test_single_file_copying_preserves_content**
   - Tests that individual files are copied with exact content preservation
   - Generates random file content and filenames
   - Verifies content and hash matching
   - Runs 100 iterations with different inputs

2. **test_directory_copying_preserves_all_files**
   - Tests that directories with multiple files are copied completely
   - Generates random number of files with random content
   - Verifies all files exist and content matches
   - Runs 100 iterations with different inputs

3. **test_nested_directory_copying_preserves_structure**
   - Tests that nested directory structures are preserved
   - Generates random subdirectory hierarchies
   - Verifies directory structure and file content
   - Handles Windows reserved names (CON, PRN, AUX, NUL, etc.)
   - Runs 100 iterations with different inputs

4. **test_lab3_component_directories_structure**
   - Tests the specific Lab3 integration directory structure
   - Validates all required components are copied:
     - processing/ (3 files)
     - extraction/ (4 files)
     - api/ (3 files)
     - storage/ (3 files + migrations)
     - normalization/ (2 files)
   - Verifies exact file count and structure

### Edge Case Tests

1. **test_empty_directory_copying**
   - Verifies empty directories can be copied

2. **test_copy_with_hidden_files**
   - Verifies hidden files (starting with .) are copied

3. **test_copy_preserves_file_permissions**
   - Verifies file content is preserved during copy

4. **test_nonexistent_source_raises_error**
   - Verifies proper error handling for invalid source

## Test Results

✅ All 8 tests passed successfully

- 3 property-based tests with 100 iterations each (300 total test cases)
- 1 integration structure test
- 4 edge case tests

## Key Features

### Hash-Based Verification
- Uses SHA256 hashing to verify file content integrity
- Ensures byte-perfect copying

### Cross-Platform Compatibility
- Filters out Windows reserved names (CON, PRN, AUX, NUL, COM1-9, LPT1-9)
- Handles path separators correctly
- Works with both regular and hidden files

### Comprehensive Coverage
- Tests single files, multiple files, and nested directories
- Tests the exact Lab3 integration structure
- Tests edge cases and error conditions

## Dependencies Added

- `hypothesis>=6.92.0` - Property-based testing framework

## Usage

Run all file copying tests:
```bash
python -m pytest tests/test_lab3_file_copying.py -v
```

Run only property-based tests:
```bash
python -m pytest tests/test_lab3_file_copying.py::TestFileCopyingProperties -v
```

Run with hypothesis statistics:
```bash
python -m pytest tests/test_lab3_file_copying.py -v --hypothesis-show-statistics
```

## Validation

These tests validate that the file copying operations required for Lab3 integration will:

1. ✅ Preserve all source files
2. ✅ Maintain directory structure
3. ✅ Keep file content identical (byte-for-byte)
4. ✅ Handle nested directories correctly
5. ✅ Copy all required Lab3 components
6. ✅ Handle edge cases gracefully

## Next Steps

The file copying functionality tested here will be used in tasks 3.1-3.5 to copy Lab3 components to the LoanQA-MLOps integration directory structure.
