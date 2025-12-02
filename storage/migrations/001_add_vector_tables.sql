-- Migration: Add Vector Store Integration Tables
-- Description: Tables for document chunks, embeddings, and chat conversations
-- Date: 2025-11-08
-- Phase: 1 - Foundation

-- ===================================
-- DOCUMENT CHUNKS TABLE
-- ===================================
CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    page_number INT,
    section_type VARCHAR(100),
    token_count INT,
    
    -- Metadata from Lab3 extraction
    related_loan_id UUID REFERENCES loans(loan_id) ON DELETE SET NULL,
    extraction_confidence DECIMAL(3, 2),
    
    -- Vector data (stored externally in ChromaDB)
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small',
    embedding_id VARCHAR(255), -- ChromaDB ID reference
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_chunk_per_doc UNIQUE(document_id, chunk_index)
);

-- ===================================
-- CHAT CONVERSATIONS TABLE
-- ===================================
CREATE TABLE IF NOT EXISTS chat_conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(document_id) ON DELETE SET NULL,
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    
    -- Conversation metadata
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_count INT DEFAULT 0,
    
    -- Context tracking
    context_document_ids UUID[],
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===================================
-- CHAT MESSAGES TABLE
-- ===================================
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES chat_conversations(conversation_id) ON DELETE CASCADE,
    
    -- Message content
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    
    -- Context used for this response
    chunks_used UUID[], -- Array of chunk_ids
    structured_data_used JSONB,
    query_type VARCHAR(50), -- 'structured', 'semantic', 'hybrid', 'calculation'
    
    -- Response metadata
    confidence DECIMAL(3, 2),
    processing_time_ms INT,
    llm_model VARCHAR(100),
    llm_provider VARCHAR(50),
    tokens_used INT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===================================
-- VECTOR SEARCH LOGS (for analytics)
-- ===================================
CREATE TABLE IF NOT EXISTS vector_search_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text TEXT NOT NULL,
    document_id UUID REFERENCES documents(document_id) ON DELETE SET NULL,
    
    -- Search parameters
    n_results INT,
    filters JSONB,
    
    -- Results
    chunk_ids_returned UUID[],
    avg_distance DECIMAL(5, 4),
    
    -- Performance
    search_time_ms INT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===================================
-- ENHANCED LOANS TABLE
-- ===================================
-- Add full-text search vector column
ALTER TABLE loans ADD COLUMN IF NOT EXISTS tsv_search tsvector;

-- ===================================
-- INDEXES FOR PERFORMANCE
-- ===================================

-- Document chunks indexes
CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_loan ON document_chunks(related_loan_id);
CREATE INDEX IF NOT EXISTS idx_chunks_page ON document_chunks(page_number);
CREATE INDEX IF NOT EXISTS idx_chunks_section ON document_chunks(section_type);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON document_chunks(embedding_id);

-- Chat indexes
CREATE INDEX IF NOT EXISTS idx_chat_conversation ON chat_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_chat_created ON chat_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON chat_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_document ON chat_conversations(document_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON chat_conversations(session_id);

-- Vector search logs
CREATE INDEX IF NOT EXISTS idx_search_logs_created ON vector_search_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_search_logs_document ON vector_search_logs(document_id);

-- Full-text search on loans
CREATE INDEX IF NOT EXISTS idx_loans_tsv ON loans USING GIN(tsv_search);

-- ===================================
-- TRIGGERS & FUNCTIONS
-- ===================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_document_chunks_updated_at 
    BEFORE UPDATE ON document_chunks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Update conversation last_message_at when new message added
CREATE OR REPLACE FUNCTION update_conversation_on_message()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE chat_conversations
    SET 
        last_message_at = CURRENT_TIMESTAMP,
        message_count = message_count + 1
    WHERE conversation_id = NEW.conversation_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_conversation_after_message
    AFTER INSERT ON chat_messages
    FOR EACH ROW EXECUTE FUNCTION update_conversation_on_message();

-- Update tsvector for full-text search on loans
CREATE OR REPLACE FUNCTION loans_tsv_trigger() 
RETURNS trigger AS $$
BEGIN
    NEW.tsv_search :=
        setweight(to_tsvector('english', COALESCE(NEW.bank_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.loan_type, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.extracted_data::text, '')), 'C');
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tsvector_update_loans ON loans;
CREATE TRIGGER tsvector_update_loans 
    BEFORE INSERT OR UPDATE ON loans
    FOR EACH ROW EXECUTE FUNCTION loans_tsv_trigger();

-- ===================================
-- VIEWS FOR EASY QUERIES
-- ===================================

-- View: Chunk with loan details
CREATE OR REPLACE VIEW v_chunks_with_context AS
SELECT 
    dc.chunk_id,
    dc.document_id,
    dc.chunk_index,
    dc.chunk_text,
    dc.page_number,
    dc.section_type,
    dc.token_count,
    dc.extraction_confidence,
    l.loan_id,
    l.bank_name,
    l.loan_type,
    l.principal_amount,
    l.interest_rate,
    l.tenure_months,
    d.file_name,
    d.upload_timestamp
FROM document_chunks dc
LEFT JOIN loans l ON dc.related_loan_id = l.loan_id
LEFT JOIN documents d ON dc.document_id = d.document_id;

-- View: Conversation summary
CREATE OR REPLACE VIEW v_conversation_summary AS
SELECT 
    cc.conversation_id,
    cc.user_id,
    cc.started_at,
    cc.last_message_at,
    cc.message_count,
    d.file_name as primary_document,
    l.bank_name,
    l.loan_type,
    l.principal_amount
FROM chat_conversations cc
LEFT JOIN documents d ON cc.document_id = d.document_id
LEFT JOIN loans l ON d.document_id = l.document_id;

-- ===================================
-- COMMENTS
-- ===================================
COMMENT ON TABLE document_chunks IS 'Stores text chunks for vector search with Lab3 extraction metadata';
COMMENT ON TABLE chat_conversations IS 'Tracks chat sessions with document context';
COMMENT ON TABLE chat_messages IS 'Stores individual messages with LLM metadata and sources';
COMMENT ON TABLE vector_search_logs IS 'Analytics for vector search performance';
COMMENT ON COLUMN loans.tsv_search IS 'Full-text search vector for fast text queries';

-- ===================================
-- COMPLETION MESSAGE
-- ===================================
DO $$
BEGIN
    RAISE NOTICE 'Migration 001_add_vector_tables.sql completed successfully';
    RAISE NOTICE 'Created tables: document_chunks, chat_conversations, chat_messages, vector_search_logs';
    RAISE NOTICE 'Created indexes for performance optimization';
    RAISE NOTICE 'Created triggers for automatic updates';
    RAISE NOTICE 'Created views for easy data access';
END $$;
