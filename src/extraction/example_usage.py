"""
Example usage of the data extraction module.
Demonstrates how to extract loan data from text and tables.
"""

from extraction_service import DataExtractionService


def example_basic_extraction():
    """Example of basic loan data extraction from text."""
    
    # Sample loan document text
    sample_text = """
    LOAN AGREEMENT
    
    Bank Name: HDFC Bank
    Branch: Mumbai Central Branch
    
    Loan Details:
    Principal Amount: Rs. 5,00,000
    Interest Rate: 10.5% p.a.
    Loan Tenure: 60 months
    Moratorium Period: 6 months
    
    Fees and Charges:
    Processing Fee: Rs. 5,000
    Documentation Charges: Rs. 1,000
    
    Penalties:
    Late Payment Penalty: 2% per month
    Prepayment Penalty: 3% of outstanding amount
    
    Repayment Mode: EMI (Equated Monthly Installment)
    EMI Amount: Rs. 10,624
    
    Disbursement: Single disbursement within 7 days
    
    Co-signer: Mr. Rajesh Kumar
    Relationship: Father
    """
    
    # Initialize extraction service
    extractor = DataExtractionService()
    
    # Extract loan data
    extracted_data = extractor.extract_loan_data(sample_text)
    
    # Print results
    print("=== Extraction Results ===\n")
    
    print("Core Fields:")
    core = extracted_data['core_fields']
    if core.get('principal_amount'):
        print(f"  Principal: ₹{core['principal_amount']['value']:,.2f}")
    if core.get('interest_rate'):
        print(f"  Interest Rate: {core['interest_rate']['value']}% p.a.")
    if core.get('tenure'):
        print(f"  Tenure: {core['tenure']['value']} months")
    if core.get('moratorium_period'):
        print(f"  Moratorium: {core['moratorium_period']['value']} months")
    
    print("\nLender Information:")
    lender = extracted_data['entities']['lender']
    if lender.get('bank_name'):
        print(f"  Bank: {lender['bank_name']}")
    if lender.get('branch_name'):
        print(f"  Branch: {lender['branch_name']}")
    
    print("\nFees:")
    for fee in extracted_data['fees']:
        print(f"  {fee['type']}: ₹{fee['value']:,.2f}")
    
    print("\nPenalties:")
    for penalty in extracted_data['penalties']:
        value_str = f"{penalty['value']}%" if penalty['value_type'] == 'percentage' else f"₹{penalty['value']:,.2f}"
        print(f"  {penalty['type']}: {value_str}")
    
    print("\nConfidence Report:")
    conf_report = extracted_data['confidence_report']
    print(f"  Overall Confidence: {conf_report['overall_confidence']:.2%}")
    print(f"  Confidence Level: {conf_report['confidence_level']}")
    print(f"  Requires Review: {conf_report['requires_review']}")
    print(f"  Fields Extracted: {conf_report['field_count']}")
    
    if conf_report['low_confidence_fields']:
        print("\n  Low Confidence Fields:")
        for field in conf_report['low_confidence_fields']:
            print(f"    - {field['field_name']}: {field['confidence']:.2%}")
    
    return extracted_data


def example_with_payment_schedule():
    """Example with payment schedule table."""
    
    sample_text = """
    Personal Loan Agreement
    
    Loan Amount: Rs. 2,00,000
    Interest Rate: 12% per annum
    Tenure: 24 months
    """
    
    # Sample payment schedule table
    sample_table = {
        'headers': ['EMI No.', 'Due Date', 'EMI Amount', 'Principal', 'Interest', 'Outstanding'],
        'rows': [
            ['1', '01-01-2024', '9,415', '7,415', '2,000', '1,92,585'],
            ['2', '01-02-2024', '9,415', '7,489', '1,926', '1,85,096'],
            ['3', '01-03-2024', '9,415', '7,564', '1,851', '1,77,532'],
        ]
    }
    
    extractor = DataExtractionService()
    extracted_data = extractor.extract_loan_data(sample_text, tables=[sample_table])
    
    print("\n=== Payment Schedule Extraction ===\n")
    
    if extracted_data['payment_schedule']:
        print(f"Total Payments: {len(extracted_data['payment_schedule'])}")
        print("\nFirst 3 Payments:")
        for entry in extracted_data['payment_schedule'][:3]:
            print(f"  Payment {entry['payment_number']}: ₹{entry['total_amount']:,.2f} on {entry['payment_date']}")
            if 'principal_component' in entry:
                print(f"    Principal: ₹{entry['principal_component']:,.2f}, Interest: ₹{entry['interest_component']:,.2f}")
    
    return extracted_data


if __name__ == "__main__":
    print("Example 1: Basic Extraction")
    print("=" * 50)
    example_basic_extraction()
    
    print("\n\n")
    print("Example 2: With Payment Schedule")
    print("=" * 50)
    example_with_payment_schedule()
