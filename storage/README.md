# Storage Service

The storage service provides a unified interface for managing document storage and loan data persistence. It integrates PostgreSQL for structured data and S3/MinIO for document storage.

## Architecture

```

 StorageService 
 (Unified Storage Interface) 

 
 
 
 DatabaseMgr ObjectStorageMgr 
 (PostgreSQL) (S3/MinIO) 
 
```

## Components

### 1. StorageService (`storage_service.py`)

Main service class that coordinates database and object storage operations.

**Key Methods:**

- `store_document()` - Store document in S3/MinIO and save metadata to PostgreSQL
- `store_extracted_data()` - Store extracted loan data in PostgreSQL
- `retrieve_document()` - Retrieve document metadata and content
- `query_loans()` - Query loans with filters
- `create_processing_job()` - Create batch processing job
- `update_processing_job()` - Update job status and progress
- `get_processing_job()` - Retrieve job details

### 2. DatabaseManager (`database.py`)

Manages PostgreSQL connections and operations using connection pooling.

**Features:**

- Connection pooling for efficient resource usage
- Context manager for automatic connection handling
- CRUD operations for documents, loans, and processing jobs
- Query builder with filters
- Transaction management

### 3. ObjectStorageManager (`object_storage.py`)

Manages S3/MinIO object storage operations.

**Features:**

- File upload/download
- Metadata management
- Presigned URL generation
- File existence checking
- Bucket management

## Database Schema

### Tables

**documents**
- `document_id` (UUID, PK)
- `file_name` (VARCHAR)
- `file_type` (VARCHAR)
- `upload_timestamp` (TIMESTAMP)
- `file_size_bytes` (BIGINT)
- `page_count` (INT)
- `storage_path` (VARCHAR)
- `processing_status` (VARCHAR)
- `created_at` (TIMESTAMP)

**loans**
- `loan_id` (UUID, PK)
- `document_id` (UUID, FK)
- `loan_type` (VARCHAR)
- `bank_name` (VARCHAR)
- `principal_amount` (DECIMAL)
- `interest_rate` (DECIMAL)
- `tenure_months` (INT)
- `extracted_data` (JSONB)
- `extraction_confidence` (DECIMAL)
- `extraction_timestamp` (TIMESTAMP)
- `created_at` (TIMESTAMP)

**comparison_metrics**
- `metric_id` (UUID, PK)
- `loan_id` (UUID, FK)
- `total_cost_estimate` (DECIMAL)
- `effective_interest_rate` (DECIMAL)
- `flexibility_score` (DECIMAL)
- `monthly_emi` (DECIMAL)
- `total_interest_payable` (DECIMAL)
- `calculated_at` (TIMESTAMP)

**processing_jobs**
- `job_id` (UUID, PK)
- `status` (VARCHAR)
- `total_documents` (INT)
- `processed_documents` (INT)
- `failed_documents` (INT)
- `created_at` (TIMESTAMP)
- `completed_at` (TIMESTAMP)
- `error_message` (TEXT)

## Usage Examples

### Initialize Storage Service

```python
from storage.storage_service import StorageService
from config import config

storage = StorageService(
 database_url=config.DATABASE_URL,
 s3_endpoint=config.S3_ENDPOINT,
 s3_access_key=config.S3_ACCESS_KEY,
 s3_secret_key=config.S3_SECRET_KEY,
 s3_bucket_name=config.S3_BUCKET_NAME,
 s3_region=config.S3_REGION
)

storage.initialize()
```

### Store a Document

```python
# Read document file
with open('loan_document.pdf', 'rb') as f:
 file_data = f.read()

# Store document
document_id = storage.store_document(
 file_data=file_data,
 file_name='loan_document.pdf',
 file_type='pdf',
 file_size_bytes=len(file_data),
 page_count=10
)
```

### Store Extracted Loan Data

```python
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
 'extraction_confidence': 0.95
}

loan_id = storage.store_extracted_data(loan_data)
```

### Query Loans

```python
filters = {
 'loan_type': 'education',
 'min_principal': 100000,
 'max_principal': 1000000,
 'bank_name': 'Example',
 'limit': 10,
 'offset': 0
}

loans = storage.query_loans(filters)
```

### Manage Processing Jobs

```python
# Create job
job_id = storage.create_processing_job(total_documents=100)

# Update progress
storage.update_processing_job(
 job_id=job_id,
 status='processing',
 processed_documents=50
)

# Get job status
job_status = storage.get_processing_job(job_id)

# Complete job
storage.update_processing_job(
 job_id=job_id,
 status='completed',
 processed_documents=100,
 completed_at=datetime.now()
)
```

### Retrieve Document

```python
result = storage.retrieve_document(document_id)

if result:
 metadata = result['metadata']
 content = result['content']
 
 print(f"File: {metadata['file_name']}")
 print(f"Status: {metadata['processing_status']}")
 print(f"Size: {len(content)} bytes")
```

## Configuration

Configure storage settings in `config.py` or via environment variables:

```python
# Database
DATABASE_URL = "postgresql://user:pass@host:5432/dbname"

# S3/MinIO
S3_ENDPOINT = "http://minio:9000"
S3_ACCESS_KEY = "minioadmin"
S3_SECRET_KEY = "minioadmin123"
S3_BUCKET_NAME = "loan-documents"
S3_REGION = "us-east-1"
```

## Error Handling

All methods include comprehensive error handling and logging:

```python
try:
 document_id = storage.store_document(...)
except Exception as e:
 logger.error(f"Failed to store document: {e}")
 # Handle error appropriately
```

## Database Initialization

Run the initialization script to create tables and indexes:

```bash
psql -U user -d loanextractor -f storage/init_db.sql
```

Or use the setup script:

```python
from storage.setup_storage import setup_database

setup_database(config.DATABASE_URL)
```

## Testing

Run the example usage script to test the storage service:

```bash
python storage/example_usage.py
```

## Requirements

- PostgreSQL 12+
- S3-compatible object storage (AWS S3 or MinIO)
- Python packages:
 - psycopg2-binary
 - boto3
 - botocore

## Performance Considerations

- **Connection Pooling**: Database connections are pooled for efficiency
- **Batch Operations**: Use processing jobs for batch document processing
- **Indexes**: Database indexes optimize query performance
- **JSONB**: Extracted data stored as JSONB for flexible querying
- **Presigned URLs**: Generate temporary URLs for secure file access

## Security

- All database connections use connection pooling with proper cleanup
- S3 operations support encryption at rest and in transit
- Presigned URLs provide time-limited access to documents
- SQL injection prevention through parameterized queries
- Proper error handling prevents information leakage

## Monitoring

The service includes comprehensive logging:

```python
import logging

logging.basicConfig(
 level=logging.INFO,
 format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Monitor these key metrics:
- Document upload success/failure rates
- Database query performance
- Storage usage
- Processing job completion rates
- Error rates by operation type
