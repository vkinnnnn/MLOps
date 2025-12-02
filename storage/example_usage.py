"""
Example usage of the storage service
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.storage_service import StorageService
from config import config
from datetime import datetime
import json


def main():
    """Demonstrate storage service usage"""
    
    # Initialize storage service
    print("Initializing storage service...")
    storage = StorageService(
        database_url=config.DATABASE_URL,
        s3_endpoint=config.S3_ENDPOINT,
        s3_access_key=config.S3_ACCESS_KEY,
        s3_secret_key=config.S3_SECRET_KEY,
        s3_bucket_name=config.S3_BUCKET_NAME,
        s3_region=config.S3_REGION
    )
    
    try:
        storage.initialize()
        print("✓ Storage service initialized successfully\n")
        
        # Example 1: Store a document
        print("Example 1: Storing a document")
        print("-" * 50)
        
        # Simulate document content
        sample_document = b"Sample loan document content"
        
        document_id = storage.store_document(
            file_data=sample_document,
            file_name="sample_loan.pdf",
            file_type="pdf",
            file_size_bytes=len(sample_document),
            page_count=5
        )
        print(f"✓ Document stored with ID: {document_id}\n")
        
        # Example 2: Store extracted loan data
        print("Example 2: Storing extracted loan data")
        print("-" * 50)
        
        loan_data = {
            'document_id': document_id,
            'loan_type': 'education',
            'bank_info': {
                'bank_name': 'Example Bank',
                'branch_name': 'Main Branch'
            },
            'principal_amount': 500000.00,
            'interest_rate': 8.5,
            'tenure_months': 120,
            'moratorium_period_months': 12,
            'fees': [
                {
                    'fee_type': 'processing',
                    'amount': 5000.00,
                    'currency': 'INR'
                }
            ],
            'extraction_confidence': 0.95,
            'extraction_timestamp': datetime.now()
        }
        
        loan_id = storage.store_extracted_data(loan_data)
        print(f"✓ Loan data stored with ID: {loan_id}\n")
        
        # Example 3: Retrieve document
        print("Example 3: Retrieving document")
        print("-" * 50)
        
        retrieved = storage.retrieve_document(document_id)
        if retrieved:
            print(f"✓ Document retrieved:")
            print(f"  - File name: {retrieved['metadata']['file_name']}")
            print(f"  - File type: {retrieved['metadata']['file_type']}")
            print(f"  - Status: {retrieved['metadata']['processing_status']}")
            print(f"  - Content size: {len(retrieved['content'])} bytes\n")
        
        # Example 4: Query loans
        print("Example 4: Querying loans")
        print("-" * 50)
        
        filters = {
            'loan_type': 'education',
            'min_principal': 100000,
            'max_principal': 1000000,
            'limit': 10
        }
        
        loans = storage.query_loans(filters)
        print(f"✓ Found {len(loans)} matching loans")
        for loan in loans:
            print(f"  - Loan ID: {loan['loan_id']}")
            print(f"    Bank: {loan.get('bank_name', 'N/A')}")
            print(f"    Principal: ₹{loan.get('principal_amount', 0):,.2f}")
            print(f"    Interest Rate: {loan.get('interest_rate', 0)}%\n")
        
        # Example 5: Create and manage processing job
        print("Example 5: Managing processing job")
        print("-" * 50)
        
        job_id = storage.create_processing_job(total_documents=10)
        print(f"✓ Processing job created with ID: {job_id}")
        
        # Update job progress
        storage.update_processing_job(
            job_id=job_id,
            status='processing',
            processed_documents=5
        )
        print(f"✓ Job updated: 5/10 documents processed")
        
        # Get job status
        job_status = storage.get_processing_job(job_id)
        if job_status:
            print(f"✓ Job status retrieved:")
            print(f"  - Status: {job_status['status']}")
            print(f"  - Progress: {job_status['processed_documents']}/{job_status['total_documents']}")
            print(f"  - Failed: {job_status['failed_documents']}\n")
        
        # Complete the job
        storage.update_processing_job(
            job_id=job_id,
            status='completed',
            processed_documents=10,
            completed_at=datetime.now()
        )
        print(f"✓ Job marked as completed\n")
        
        print("=" * 50)
        print("All examples completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        storage.close()
        print("\n✓ Storage service closed")


if __name__ == "__main__":
    main()
