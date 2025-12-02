# Data Extraction Module

This module provides comprehensive data extraction capabilities for loan documents, extracting structured information from OCR text and table data.

## Components

### 1. CoreLoanFieldExtractor (`field_extractor.py`)
Extracts core loan terms using pattern matching:
- **Principal Amount**: Loan amount with currency
- **Interest Rate**: Annual interest rate or APR
- **Tenure**: Loan period in months/years
- **Moratorium Period**: Grace period before repayment

### 2. FeeAndPenaltyExtractor (`fee_extractor.py`)
Extracts fees and penalty information:
- **Processing Fees**: Fixed amount or percentage
- **Administrative Fees**: Admin charges
- **Documentation Fees**: Document processing charges
- **Late Payment Penalties**: Penalties for delayed payments
- **Prepayment Penalties**: Charges for early repayment
- **Table-based Fee Extraction**: Extracts fees from structured tables

### 3. EntityExtractor (`entity_extractor.py`)
Extracts lender and borrower information:
- **Bank Name**: Lender institution identification
- **Branch Details**: Branch name and location
- **Co-signer Details**: Guarantor name and relationship
- **Collateral Details**: Security/pledge information

### 4. PaymentScheduleExtractor (`schedule_extractor.py`)
Extracts payment schedules from tables:
- **Payment Dates**: Due dates for each installment
- **Payment Amounts**: Total EMI/installment amounts
- **Principal/Interest Components**: Breakdown of each payment
- **Outstanding Balance**: Remaining loan balance
- **Schedule Summary**: Aggregate statistics

### 5. AdditionalTermsExtractor (`terms_extractor.py`)
Extracts additional loan terms:
- **Disbursement Terms**: Single or multiple disbursement
- **Repayment Mode**: EMI, bullet payment, or step-up
- **EMI Amount**: Monthly installment amount
- **Prepayment Options**: Foreclosure allowance
- **Lock-in Period**: Minimum loan period

### 6. ConfidenceScorer (`confidence_scorer.py`)
Calculates confidence scores for extracted data:
- **Field-level Confidence**: Individual field reliability scores
- **Overall Confidence**: Weighted aggregate confidence
- **Low Confidence Flagging**: Identifies fields needing review
- **Missing Field Detection**: Identifies critical missing data

### 7. DataExtractionService (`extraction_service.py`)
Main orchestration service that:
- Coordinates all extractors
- Provides unified extraction interface
- Generates confidence reports
- Produces extraction summaries

## Usage

### Basic Usage

```python
from extraction import DataExtractionService

# Initialize service
extractor = DataExtractionService()

# Extract from text only
extracted_data = extractor.extract_loan_data(ocr_text)

# Extract from text and tables
extracted_data = extractor.extract_loan_data(ocr_text, tables=table_list)

# Access extracted data
core_fields = extracted_data['core_fields']
fees = extracted_data['fees']
penalties = extracted_data['penalties']
entities = extracted_data['entities']
payment_schedule = extracted_data['payment_schedule']
confidence_report = extracted_data['confidence_report']
```

### Specialized Extraction

```python
# Extract only core fields
core_data = extractor.extract_core_fields_only(text)

# Extract only fees and penalties
fees_data = extractor.extract_fees_and_penalties_only(text, tables)

# Extract only payment schedule
schedule = extractor.extract_payment_schedule_only(tables)

# Get extraction summary
summary = extractor.get_extraction_summary(extracted_data)
```

## Data Structure

### Extracted Data Format

```python
{
 'core_fields': {
 'principal_amount': {
 'value': 500000.0,
 'currency': 'INR',
 'confidence': 0.9,
 'source_text': 'Principal Amount: Rs. 5,00,000'
 },
 'interest_rate': {
 'value': 10.5,
 'unit': 'percent_per_annum',
 'confidence': 0.9,
 'source_text': 'Interest Rate: 10.5% p.a.'
 },
 'tenure': {
 'value': 60,
 'unit': 'months',
 'confidence': 0.9
 },
 'moratorium_period': {
 'value': 6,
 'unit': 'months',
 'confidence': 0.85
 }
 },
 'fees': [
 {
 'type': 'processing_fee',
 'value': 5000.0,
 'value_type': 'fixed',
 'currency': 'INR',
 'confidence': 0.85
 }
 ],
 'penalties': [
 {
 'type': 'late_payment_penalty',
 'value': 2.0,
 'value_type': 'percentage',
 'confidence': 0.8
 }
 ],
 'entities': {
 'lender': {
 'bank_name': 'HDFC Bank',
 'branch_name': 'Mumbai Central Branch',
 'bank_confidence': 0.95
 },
 'cosigner': {
 'name': 'Mr. Rajesh Kumar',
 'relationship': 'father',
 'confidence': 0.8
 },
 'collateral': {
 'type': 'property',
 'description': 'Residential property',
 'confidence': 0.75
 }
 },
 'payment_schedule': [
 {
 'payment_number': 1,
 'payment_date': '2024-01-01',
 'total_amount': 9415.0,
 'principal_component': 7415.0,
 'interest_component': 2000.0,
 'outstanding_balance': 192585.0,
 'confidence': 0.9
 }
 ],
 'additional_terms': {
 'disbursement_terms': {
 'type': 'single',
 'description': 'Single disbursement',
 'confidence': 0.8
 },
 'repayment_mode': {
 'mode': 'EMI',
 'description': 'Equated Monthly Installment',
 'confidence': 0.9
 }
 },
 'confidence_report': {
 'overall_confidence': 0.875,
 'confidence_level': 'high',
 'requires_review': False,
 'field_count': 15,
 'low_confidence_fields': [],
 'missing_critical_fields': []
 }
}
```

## Confidence Scoring

The confidence scorer uses weighted scoring based on field importance:

- **Critical Fields** (20% weight each): Principal amount, Interest rate
- **Important Fields** (15% weight): Tenure
- **Standard Fields** (5-10% weight): Fees, penalties, repayment mode
- **Optional Fields** (2-5% weight): Co-signer, collateral

### Confidence Levels
- **High**: ≥ 90% - Data is highly reliable
- **Medium**: 70-89% - Data is generally reliable, minor review recommended
- **Low**: < 70% - Data requires manual review

## Pattern Matching

The extractors use regex patterns optimized for Indian loan documents:

- Currency formats: Rs., INR, ₹
- Number formats: With/without commas (e.g., 5,00,000 or 500000)
- Date formats: DD-MM-YYYY, DD/MM/YYYY, DD Mon YYYY
- Percentage formats: With/without % symbol

## Requirements Mapping

This module satisfies the following requirements:

- **Requirement 2.1-2.13**: Document content extraction
- **Requirement 3A.11**: Payment schedule extraction
- **Requirement 3A.12**: Fee structure extraction

## Example

See `example_usage.py` for complete working examples.

## Future Enhancements

- Named Entity Recognition (NER) integration for improved entity extraction
- Machine learning models for context-aware extraction
- Multi-language support
- Custom pattern configuration
- Extraction rule learning from corrections
