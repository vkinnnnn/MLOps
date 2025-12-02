"""
Test search and navigation functionality
"""
import sys
import os
from datetime import datetime, timedelta, date

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../dashboard/components')))

from dashboard.components.search import (
    filter_documents,
    sort_documents,
    get_unique_loan_types,
    get_unique_bank_names
)


def create_sample_documents():
    """Create sample documents for testing"""
    today = datetime.now().date()
    
    return [
        {
            "name": "education_loan_1.pdf",
            "size": 1024000,
            "type": "application/pdf",
            "upload_date": today,
            "extracted_data": {
                "loan_type": "Education Loan",
                "bank_name": "ABC Bank",
                "principal_amount": 50000,
                "interest_rate": 7.5,
                "tenure_months": 120
            }
        },
        {
            "name": "home_loan_1.pdf",
            "size": 2048000,
            "type": "application/pdf",
            "upload_date": today - timedelta(days=5),
            "extracted_data": {
                "loan_type": "Home Loan",
                "bank_name": "XYZ Bank",
                "principal_amount": 200000,
                "interest_rate": 6.5,
                "tenure_months": 240
            }
        },
        {
            "name": "personal_loan_1.pdf",
            "size": 512000,
            "type": "application/pdf",
            "upload_date": today - timedelta(days=15),
            "extracted_data": {
                "loan_type": "Personal Loan",
                "bank_name": "ABC Bank",
                "principal_amount": 25000,
                "interest_rate": 10.5,
                "tenure_months": 60
            }
        },
        {
            "name": "education_loan_2.pdf",
            "size": 1536000,
            "type": "application/pdf",
            "upload_date": today - timedelta(days=35),
            "extracted_data": {
                "loan_type": "Education Loan",
                "bank_name": "DEF Bank",
                "principal_amount": 75000,
                "interest_rate": 8.0,
                "tenure_months": 180
            }
        }
    ]


def test_get_unique_loan_types():
    """Test extracting unique loan types"""
    print("Testing get_unique_loan_types...")
    
    documents = create_sample_documents()
    loan_types = get_unique_loan_types(documents)
    
    assert len(loan_types) == 3, f"Expected 3 loan types, got {len(loan_types)}"
    assert "Education Loan" in loan_types, "Education Loan not found"
    assert "Home Loan" in loan_types, "Home Loan not found"
    assert "Personal Loan" in loan_types, "Personal Loan not found"
    
    print("✓ get_unique_loan_types test passed")


def test_get_unique_bank_names():
    """Test extracting unique bank names"""
    print("Testing get_unique_bank_names...")
    
    documents = create_sample_documents()
    bank_names = get_unique_bank_names(documents)
    
    assert len(bank_names) == 3, f"Expected 3 banks, got {len(bank_names)}"
    assert "ABC Bank" in bank_names, "ABC Bank not found"
    assert "XYZ Bank" in bank_names, "XYZ Bank not found"
    assert "DEF Bank" in bank_names, "DEF Bank not found"
    
    print("✓ get_unique_bank_names test passed")


def test_filter_by_search_query():
    """Test filtering by search query"""
    print("Testing filter by search query...")
    
    documents = create_sample_documents()
    
    # Search for "education"
    filtered = filter_documents(documents, search_query="education")
    assert len(filtered) == 2, f"Expected 2 education loans, got {len(filtered)}"
    
    # Search for "home"
    filtered = filter_documents(documents, search_query="home")
    assert len(filtered) == 1, f"Expected 1 home loan, got {len(filtered)}"
    
    print("✓ filter by search query test passed")


def test_filter_by_loan_type():
    """Test filtering by loan type"""
    print("Testing filter by loan type...")
    
    documents = create_sample_documents()
    
    # Filter by Education Loan
    filtered = filter_documents(documents, loan_type="Education Loan")
    assert len(filtered) == 2, f"Expected 2 education loans, got {len(filtered)}"
    
    # Filter by Home Loan
    filtered = filter_documents(documents, loan_type="Home Loan")
    assert len(filtered) == 1, f"Expected 1 home loan, got {len(filtered)}"
    
    print("✓ filter by loan type test passed")


def test_filter_by_bank_name():
    """Test filtering by bank name"""
    print("Testing filter by bank name...")
    
    documents = create_sample_documents()
    
    # Filter by ABC Bank
    filtered = filter_documents(documents, bank_name="ABC Bank")
    assert len(filtered) == 2, f"Expected 2 loans from ABC Bank, got {len(filtered)}"
    
    # Filter by XYZ Bank
    filtered = filter_documents(documents, bank_name="XYZ Bank")
    assert len(filtered) == 1, f"Expected 1 loan from XYZ Bank, got {len(filtered)}"
    
    print("✓ filter by bank name test passed")


def test_filter_by_date():
    """Test filtering by date range"""
    print("Testing filter by date...")
    
    documents = create_sample_documents()
    
    # Filter by "Today"
    filtered = filter_documents(documents, date_filter="Today")
    assert len(filtered) == 1, f"Expected 1 document from today, got {len(filtered)}"
    
    # Filter by "Last 7 Days"
    filtered = filter_documents(documents, date_filter="Last 7 Days")
    assert len(filtered) == 2, f"Expected 2 documents from last 7 days, got {len(filtered)}"
    
    # Filter by "Last 30 Days"
    filtered = filter_documents(documents, date_filter="Last 30 Days")
    assert len(filtered) == 3, f"Expected 3 documents from last 30 days, got {len(filtered)}"
    
    print("✓ filter by date test passed")


def test_sort_by_name():
    """Test sorting by name"""
    print("Testing sort by name...")
    
    documents = create_sample_documents()
    
    # Sort A-Z
    sorted_docs = sort_documents(documents, "Name (A-Z)")
    assert sorted_docs[0]["name"] == "education_loan_1.pdf", "First document should be education_loan_1.pdf"
    
    # Sort Z-A
    sorted_docs = sort_documents(documents, "Name (Z-A)")
    assert sorted_docs[0]["name"] == "personal_loan_1.pdf", "First document should be personal_loan_1.pdf"
    
    print("✓ sort by name test passed")


def test_sort_by_principal():
    """Test sorting by principal amount"""
    print("Testing sort by principal amount...")
    
    documents = create_sample_documents()
    
    # Sort High-Low
    sorted_docs = sort_documents(documents, "Principal Amount (High-Low)")
    assert sorted_docs[0]["extracted_data"]["principal_amount"] == 200000, "Highest principal should be 200000"
    
    # Sort Low-High
    sorted_docs = sort_documents(documents, "Principal Amount (Low-High)")
    assert sorted_docs[0]["extracted_data"]["principal_amount"] == 25000, "Lowest principal should be 25000"
    
    print("✓ sort by principal amount test passed")


def test_sort_by_interest_rate():
    """Test sorting by interest rate"""
    print("Testing sort by interest rate...")
    
    documents = create_sample_documents()
    
    # Sort High-Low
    sorted_docs = sort_documents(documents, "Interest Rate (High-Low)")
    assert sorted_docs[0]["extracted_data"]["interest_rate"] == 10.5, "Highest rate should be 10.5"
    
    # Sort Low-High
    sorted_docs = sort_documents(documents, "Interest Rate (Low-High)")
    assert sorted_docs[0]["extracted_data"]["interest_rate"] == 6.5, "Lowest rate should be 6.5"
    
    print("✓ sort by interest rate test passed")


def test_combined_filters():
    """Test combining multiple filters"""
    print("Testing combined filters...")
    
    documents = create_sample_documents()
    
    # Filter by loan type and bank
    filtered = filter_documents(
        documents,
        loan_type="Education Loan",
        bank_name="ABC Bank"
    )
    assert len(filtered) == 1, f"Expected 1 document, got {len(filtered)}"
    assert filtered[0]["name"] == "education_loan_1.pdf", "Should be education_loan_1.pdf"
    
    print("✓ combined filters test passed")


def run_all_tests():
    """Run all search functionality tests"""
    print("\n" + "="*60)
    print("Running Search Functionality Tests")
    print("="*60 + "\n")
    
    try:
        test_get_unique_loan_types()
        test_get_unique_bank_names()
        test_filter_by_search_query()
        test_filter_by_loan_type()
        test_filter_by_bank_name()
        test_filter_by_date()
        test_sort_by_name()
        test_sort_by_principal()
        test_sort_by_interest_rate()
        test_combined_filters()
        
        print("\n" + "="*60)
        print("✓ All tests passed successfully!")
        print("="*60 + "\n")
        return True
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
