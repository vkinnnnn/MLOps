"""
Example usage of the batch processing handler.

This script demonstrates how to use the BatchProcessingHandler to process
multiple loan documents in batch mode.
"""

import logging
from pathlib import Path
from batch_processor import BatchProcessingHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_batch_processing_from_directory():
    """
    Example: Process all documents from a directory.
    """
    # Initialize batch processor
    batch_processor = BatchProcessingHandler()
    
    # Get all PDF files from sample directory
    sample_dir = Path("../sample-loan-docs")
    
    if not sample_dir.exists():
        logger.error(f"Sample directory not found: {sample_dir}")
        return
    
    # Get list of PDF files
    pdf_files = list(sample_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning("No PDF files found in sample directory")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Convert to string paths
    file_paths = [str(f) for f in pdf_files[:5]]  # Process first 5 files as example
    
    # Process batch
    logger.info("Starting batch processing...")
    summary = batch_processor.process_batch_from_paths(
        file_paths=file_paths,
        continue_on_failure=True
    )
    
    # Print summary
    print("\n" + "="*80)
    print("BATCH PROCESSING SUMMARY")
    print("="*80)
    print(f"Job ID: {summary.job_id}")
    print(f"Total Documents: {summary.total_documents}")
    print(f"Processed: {summary.processed_documents}")
    print(f"Successful: {summary.successful_documents}")
    print(f"Failed: {summary.failed_documents}")
    print(f"Total Processing Time: {summary.get_total_processing_time():.2f} seconds")
    print("\n" + "-"*80)
    print("INDIVIDUAL RESULTS:")
    print("-"*80)
    
    for result in summary.results:
        status_symbol = "✓" if result.status == "success" else "✗"
        print(f"{status_symbol} {result.file_name}")
        print(f"  Status: {result.status}")
        if result.document_id:
            print(f"  Document ID: {result.document_id}")
        if result.loan_id:
            print(f"  Loan ID: {result.loan_id}")
        if result.error_message:
            print(f"  Error: {result.error_message}")
        if result.processing_time:
            print(f"  Processing Time: {result.processing_time:.2f}s")
        print()
    
    print("="*80)


def example_batch_processing_from_bytes():
    """
    Example: Process documents from byte data.
    """
    # Initialize batch processor
    batch_processor = BatchProcessingHandler()
    
    # Read some sample files
    sample_dir = Path("../sample-loan-docs")
    
    if not sample_dir.exists():
        logger.error(f"Sample directory not found: {sample_dir}")
        return
    
    pdf_files = list(sample_dir.glob("*.pdf"))[:3]  # First 3 files
    
    if not pdf_files:
        logger.warning("No PDF files found")
        return
    
    # Prepare documents list
    documents = []
    for pdf_file in pdf_files:
        with open(pdf_file, 'rb') as f:
            file_data = f.read()
        
        documents.append({
            'file_name': pdf_file.name,
            'file_data': file_data
        })
    
    logger.info(f"Processing {len(documents)} documents from byte data")
    
    # Process batch
    summary = batch_processor.process_batch_from_bytes(
        documents=documents,
        continue_on_failure=True
    )
    
    # Print summary
    print("\n" + "="*80)
    print("BATCH PROCESSING SUMMARY (FROM BYTES)")
    print("="*80)
    print(f"Job ID: {summary.job_id}")
    print(f"Successful: {summary.successful_documents}/{summary.total_documents}")
    print(f"Failed: {summary.failed_documents}/{summary.total_documents}")
    print(f"Total Time: {summary.get_total_processing_time():.2f}s")
    print("="*80)


def example_check_job_status():
    """
    Example: Check the status of a batch processing job.
    """
    batch_processor = BatchProcessingHandler()
    
    # Replace with actual job ID
    job_id = "your-job-id-here"
    
    status = batch_processor.get_job_status(job_id)
    
    if status:
        print("\n" + "="*80)
        print("JOB STATUS")
        print("="*80)
        print(f"Job ID: {status['job_id']}")
        print(f"Status: {status['status']}")
        print(f"Progress: {status['processed_documents']}/{status['total_documents']}")
        print(f"Failed: {status['failed_documents']}")
        print(f"Created: {status['created_at']}")
        if status['completed_at']:
            print(f"Completed: {status['completed_at']}")
        print("="*80)
    else:
        print(f"Job not found: {job_id}")


if __name__ == "__main__":
    print("Batch Processing Handler Examples")
    print("="*80)
    print("\n1. Processing from directory")
    print("2. Processing from byte data")
    print("3. Check job status")
    
    choice = input("\nSelect example (1-3): ").strip()
    
    if choice == "1":
        example_batch_processing_from_directory()
    elif choice == "2":
        example_batch_processing_from_bytes()
    elif choice == "3":
        example_check_job_status()
    else:
        print("Invalid choice")
