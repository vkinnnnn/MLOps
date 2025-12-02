-- Database initialization script for Student Loan Document Extractor Platform

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    document_id UUID PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    upload_timestamp TIMESTAMP NOT NULL,
    file_size_bytes BIGINT,
    page_count INT,
    storage_path VARCHAR(500) NOT NULL,
    processing_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create loans table
CREATE TABLE IF NOT EXISTS loans (
    loan_id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    loan_type VARCHAR(50) NOT NULL,
    bank_name VARCHAR(255),
    principal_amount DECIMAL(15, 2),
    interest_rate DECIMAL(5, 2),
    tenure_months INT,
    extracted_data JSONB NOT NULL,
    extraction_confidence DECIMAL(3, 2),
    extraction_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create comparison metrics table
CREATE TABLE IF NOT EXISTS comparison_metrics (
    metric_id UUID PRIMARY KEY,
    loan_id UUID REFERENCES loans(loan_id) ON DELETE CASCADE,
    total_cost_estimate DECIMAL(15, 2),
    effective_interest_rate DECIMAL(5, 2),
    flexibility_score DECIMAL(3, 1),
    monthly_emi DECIMAL(15, 2),
    total_interest_payable DECIMAL(15, 2),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create processing jobs table (for batch processing)
CREATE TABLE IF NOT EXISTS processing_jobs (
    job_id UUID PRIMARY KEY,
    status VARCHAR(50) DEFAULT 'queued',
    total_documents INT NOT NULL,
    processed_documents INT DEFAULT 0,
    failed_documents INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_loans_document_id ON loans(document_id);
CREATE INDEX IF NOT EXISTS idx_loans_loan_type ON loans(loan_type);
CREATE INDEX IF NOT EXISTS idx_loans_bank_name ON loans(bank_name);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_upload_timestamp ON documents(upload_timestamp);
CREATE INDEX IF NOT EXISTS idx_loans_created_at ON loans(created_at);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status);

-- Create GIN index for JSONB queries
CREATE INDEX IF NOT EXISTS idx_loans_extracted_data ON loans USING GIN (extracted_data);

-- Add comments to tables
COMMENT ON TABLE documents IS 'Stores metadata for uploaded loan documents';
COMMENT ON TABLE loans IS 'Stores extracted and normalized loan data';
COMMENT ON TABLE comparison_metrics IS 'Stores calculated comparison metrics for loans';
COMMENT ON TABLE processing_jobs IS 'Tracks batch processing jobs';
