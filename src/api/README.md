# Student Loan Document Extractor API

REST API for the Student Loan Document Extractor Platform, built with FastAPI.

## Overview

This API provides endpoints for:
- Uploading loan documents (single and batch)
- Retrieving document metadata and extracted data
- Querying loans with filters
- Comparing multiple loan offers
- Tracking batch processing status

## Installation

```bash
pip install -r requirements.txt
```

## Running the API

### Development Mode

```bash
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Health Check

- **GET** `/health` - Health check endpoint
- **GET** `/` - API information and available endpoints

### Document Upload

- **POST** `/api/v1/documents/upload` - Upload a single loan document
 - Accepts: PDF, JPEG, PNG, TIFF files
 - Returns: Document ID and processing status
 
- **POST** `/api/v1/documents/batch-upload` - Upload multiple documents
 - Accepts: Up to 50 files per batch
 - Returns: Job ID for tracking batch processing

### Document Retrieval

- **GET** `/api/v1/documents/{document_id}` - Get document metadata
 - Returns: File information, upload timestamp, processing status
 
- **GET** `/api/v1/documents/{document_id}/extracted-data` - Get extracted loan data
 - Returns: Structured loan information (principal, interest rate, fees, etc.)

### Loan Query

- **GET** `/api/v1/loans` - Query loans with filters
 - Query Parameters:
 - `loan_type`: Filter by loan type (education, home, personal, vehicle, gold)
 - `bank_name`: Filter by bank name
 - `min_principal`: Minimum principal amount
 - `max_principal`: Maximum principal amount
 - `min_interest_rate`: Minimum interest rate
 - `max_interest_rate`: Maximum interest rate
 - `limit`: Number of results (default: 10, max: 100)
 - `offset`: Pagination offset (default: 0)

### Loan Comparison

- **POST** `/api/v1/compare` - Compare multiple loan offers
 - Request Body: `{"loan_ids": ["id1", "id2", ...]}`
 - Returns: Comparison metrics, best options by cost and flexibility

### Processing Status

- **GET** `/api/v1/processing-status/{job_id}` - Get batch processing status
 - Returns: Job status, progress, and error messages

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Request/Response Examples

### Upload Document

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
 -H "Content-Type: multipart/form-data" \
 -F "file=@loan_document.pdf"
```

Response:
```json
{
 "success": true,
 "document_id": "123e4567-e89b-12d3-a456-426614174000",
 "message": "Document uploaded successfully and queued for processing",
 "file_name": "loan_document.pdf",
 "processing_status": "pending"
}
```

### Compare Loans

```bash
curl -X POST "http://localhost:8000/api/v1/compare" \
 -H "Content-Type: application/json" \
 -d '{"loan_ids": ["loan1", "loan2"]}'
```

Response:
```json
{
 "loans": [...],
 "metrics": [...],
 "best_by_cost": "loan1",
 "best_by_flexibility": "loan2",
 "comparison_notes": {
 "summary": "Comparison completed successfully"
 }
}
```

## Error Handling

The API returns structured error responses:

```json
{
 "success": false,
 "error_type": "validation_error",
 "message": "Request validation failed",
 "details": {
 "errors": [...],
 "path": "/api/v1/documents/upload"
 }
}
```

Error types:
- `validation_error` - Invalid request data
- `http_error` - HTTP-level errors (404, 400, etc.)
- `internal_error` - Server-side errors

## CORS Configuration

CORS is configured to allow all origins in development. For production, update the `allow_origins` setting in `main.py`:

```python
app.add_middleware(
 CORSMiddleware,
 allow_origins=["https://yourdomain.com"],
 allow_credentials=True,
 allow_methods=["*"],
 allow_headers=["*"],
)
```

## Logging

Logs are written to:
- Console (stdout)
- File: `api.log`

Log format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

## Architecture

```
api/
 main.py # FastAPI application and configuration
 routes.py # API endpoint definitions
 models.py # Pydantic request/response models
 error_handlers.py # Global exception handlers
 README.md # This file
```

## Next Steps

To complete the API implementation:

1. **Storage Integration**: Connect to PostgreSQL database and S3/MinIO object storage
2. **Processing Pipeline**: Integrate with OCR, extraction, and normalization services
3. **Queue System**: Implement background job processing for document extraction
4. **Authentication**: Add JWT-based authentication and authorization
5. **Rate Limiting**: Implement rate limiting for API endpoints
6. **Monitoring**: Add metrics collection and monitoring

## Requirements

See `requirements.txt` for full list of dependencies:
- fastapi>=0.104.0
- uvicorn>=0.24.0
- python-multipart>=0.0.6
- pydantic>=2.4.0
- sqlalchemy>=2.0.0
- boto3>=1.28.0
