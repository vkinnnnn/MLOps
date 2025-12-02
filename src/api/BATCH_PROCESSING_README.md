# Batch Processing Handler

## Overview

The Batch Processing Handler provides functionality to process multiple loan documents in batch mode. It processes documents sequentially, handles failures gracefully, and generates comprehensive summary reports.

## Features

- **Sequential Processing**: Processes documents one at a time to ensure reliability
- **Failure Handling**: Continues processing remaining documents even if individual documents fail
- **Comprehensive Logging**: Logs all errors with diagnostic information for troubleshooting
- **Summary Reports**: Generates detailed reports with processing status for each document
- **Job Tracking**: Creates database records to track batch processing jobs
- **Flexible Input**: Accepts documents from file paths or byte data

## Requirements

This module satisfies the following requirements from the specification:

- **11.1**: Accept multiple loan documents for batch processing
- **11.2**: Process each loan document sequentially
- **11.3**: Generate a summary report listing all processed documents and their status
- **11.4**: Continue processing remaining documents if a loan document fails
- **11.5**: Log errors for failed documents with diagnostic information

## Architecture

The batch processing handler integrates with existing services:

```
BatchProcessingHandler
 DocumentUploadHandler (validation & upload)
 DataExtractionService (OCR & extraction)
 NormalizationService (data normalization)
 StorageService (database & object storage)
```

## Usage

### Basic Usage

```python
from api.batch_processor import BatchProcessingHandler

# Initialize handler
batch_processor = BatchProcessingHandler()

# Process documents from file paths
file_paths = [
 "path/to/document1.pdf",
 "path/to/document2.pdf",
 "path/to/document3.pdf"
]

summary = batch_processor.process_batch_from_paths(
 file_paths=file_paths,
 continue_on_failure=True
)

# Access results
print(f"Processed: {summary.processed_documents}")
print(f"Successful: {summary.successful_documents}")
print(f"Failed: {summary.failed_documents}")
```

### Processing from Byte Data

```python
# Prepare documents as byte data
documents = [
 {
 'file_name': 'loan1.pdf',
 'file_data': b'...' # PDF bytes
 },
 {
 'file_name': 'loan2.pdf',
 'file_data': b'...' # PDF bytes
 }
]

summary = batch_processor.process_batch_from_bytes(
 documents=documents,
 continue_on_failure=True
)
```

### Checking Job Status

```python
# Get job status by ID
job_status = batch_processor.get_job_status(job_id)

if job_status:
 print(f"Status: {job_status['status']}")
 print(f"Progress: {job_status['processed_documents']}/{job_status['total_documents']}")
```

## API Reference

### BatchProcessingHandler

Main class for batch processing operations.

#### Methods

##### `process_batch_from_paths(file_paths, continue_on_failure=True)`

Process multiple documents from file paths.

**Parameters:**
- `file_paths` (List[str]): List of file paths to process
- `continue_on_failure` (bool): Whether to continue if a document fails (default: True)

**Returns:**
- `BatchProcessingSummary`: Summary object with processing results

##### `process_batch_from_bytes(documents, continue_on_failure=True)`

Process multiple documents from byte data.

**Parameters:**
- `documents` (List[Dict]): List of dictionaries with 'file_name' and 'file_data' keys
- `continue_on_failure` (bool): Whether to continue if a document fails (default: True)

**Returns:**
- `BatchProcessingSummary`: Summary object with processing results

##### `get_job_status(job_id)`

Get the status of a batch processing job.

**Parameters:**
- `job_id` (str): Job UUID

**Returns:**
- `Dict[str, Any]`: Job status dictionary or None if not found

### BatchProcessingSummary

Summary report for batch processing operations.

#### Attributes

- `job_id` (str): Unique identifier for the batch job
- `total_documents` (int): Total number of documents to process
- `processed_documents` (int): Number of documents processed
- `successful_documents` (int): Number of successfully processed documents
- `failed_documents` (int): Number of failed documents
- `results` (List[BatchProcessingResult]): List of individual processing results
- `start_time` (datetime): When processing started
- `end_time` (datetime): When processing completed

#### Methods

##### `to_dict()`

Convert summary to dictionary format.

**Returns:**
- `Dict[str, Any]`: Dictionary representation of the summary

##### `get_total_processing_time()`

Get total processing time in seconds.

**Returns:**
- `float`: Total time in seconds

### BatchProcessingResult

Result of processing a single document.

#### Attributes

- `file_name` (str): Name of the processed file
- `status` (str): Processing status ('success', 'failed', 'skipped')
- `document_id` (str): Document ID if successfully uploaded
- `loan_id` (str): Loan ID if successfully extracted
- `error_message` (str): Error message if processing failed
- `error_type` (str): Type of error (validation, extraction, storage, etc.)
- `processing_time` (float): Time taken to process in seconds
- `timestamp` (datetime): When processing occurred

#### Methods

##### `to_dict()`

Convert result to dictionary format.

**Returns:**
- `Dict[str, Any]`: Dictionary representation of the result

## Error Handling

The batch processor handles various types of errors:

### Validation Errors

Occur when document format, size, or page count validation fails.

```python
{
 'error_type': 'validation_error',
 'error_message': 'File size exceeds maximum allowed size'
}
```

### Processing Errors

Occur during OCR, extraction, or normalization.

```python
{
 'error_type': 'processing_error',
 'error_message': 'Failed to extract text from document'
}
```

### Unexpected Errors

Catch-all for unexpected exceptions.

```python
{
 'error_type': 'unexpected_error',
 'error_message': 'Database connection failed'
}
```

## Logging

The batch processor uses Python's logging module with the following levels:

- **INFO**: High-level progress updates
- **DEBUG**: Detailed processing steps
- **WARNING**: Non-fatal issues (e.g., validation failures)
- **ERROR**: Fatal errors with full tracebacks

### Example Log Output

```
2024-01-15 10:30:00 - batch_processor - INFO - Starting batch processing job abc123 with 5 documents
2024-01-15 10:30:01 - batch_processor - INFO - Processing document: loan1.pdf
2024-01-15 10:30:02 - batch_processor - DEBUG - Uploading document: loan1.pdf
2024-01-15 10:30:03 - batch_processor - DEBUG - Storing document def456 in storage
2024-01-15 10:30:04 - batch_processor - INFO - Document loan1.pdf processed: success
2024-01-15 10:30:05 - batch_processor - WARNING - Validation error for loan2.pdf: File size exceeds limit
2024-01-15 10:30:06 - batch_processor - INFO - Batch processing job abc123 completed: 4 successful, 1 failed
```

## Database Integration

The batch processor creates and updates records in the `processing_jobs` table:

```sql
CREATE TABLE processing_jobs (
 job_id UUID PRIMARY KEY,
 status VARCHAR(50) DEFAULT 'queued',
 total_documents INT,
 processed_documents INT DEFAULT 0,
 failed_documents INT DEFAULT 0,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 completed_at TIMESTAMP
);
```

### Job Statuses

- `queued`: Job created but not started
- `processing`: Job is currently processing documents
- `completed`: Job completed successfully (all documents processed)
- `completed_with_errors`: Job completed but some documents failed
- `failed`: Job failed completely

## Performance Considerations

### Sequential Processing

Documents are processed sequentially (one at a time) to:
- Ensure reliable error handling
- Prevent resource exhaustion
- Maintain clear audit trails
- Simplify debugging

### Processing Time

Average processing time per document depends on:
- Document size and page count
- OCR complexity
- Database and storage latency

Typical times:
- Small documents (1-5 pages): 5-10 seconds
- Medium documents (6-20 pages): 10-30 seconds
- Large documents (21-50 pages): 30-60 seconds

### Scalability

For large batches:
- Consider splitting into smaller batches
- Monitor database connection pool
- Ensure adequate storage space
- Review log file sizes

## Examples

See `batch_processor_example.py` for complete working examples:

1. Processing from directory
2. Processing from byte data
3. Checking job status

## Testing

To test the batch processor:

```python
# Create test documents
test_files = [
 "test_data/valid_loan.pdf",
 "test_data/invalid_format.txt", # Should fail validation
 "test_data/large_loan.pdf"
]

# Process with failure handling
handler = BatchProcessingHandler()
summary = handler.process_batch_from_paths(test_files)

# Verify results
assert summary.total_documents == 3
assert summary.successful_documents >= 1
assert summary.failed_documents >= 1
```

## Troubleshooting

### Common Issues

**Issue**: All documents failing with validation errors
- Check file formats are supported (PDF, JPEG, PNG, TIFF)
- Verify file sizes are under 50MB
- Ensure page counts are under 50 pages

**Issue**: Processing is very slow
- Check database connection performance
- Verify object storage is accessible
- Review OCR service performance
- Check available system resources

**Issue**: Job status not updating
- Verify database connection
- Check for transaction rollbacks
- Review error logs for exceptions

## Future Enhancements

Potential improvements for future versions:

1. **Parallel Processing**: Process multiple documents concurrently
2. **Priority Queue**: Allow prioritization of certain documents
3. **Resume Capability**: Resume failed batch jobs
4. **Progress Callbacks**: Real-time progress notifications
5. **Batch Comparison**: Automatically compare all loans in a batch
6. **Export Reports**: Generate PDF/Excel reports of batch results

## Related Documentation

- [Document Ingestion](document_ingestion.py)
- [Extraction Service](../extraction/extraction_service.py)
- [Normalization Service](../normalization/normalization_service.py)
- [Storage Service](../storage/storage_service.py)
