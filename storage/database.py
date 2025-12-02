"""
Database connection and operations module
"""
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import SimpleConnectionPool
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL database connections and operations"""
    
    def __init__(self, database_url: str, min_conn: int = 1, max_conn: int = 10):
        """
        Initialize database manager with connection pool
        
        Args:
            database_url: PostgreSQL connection URL
            min_conn: Minimum number of connections in pool
            max_conn: Maximum number of connections in pool
        """
        self.database_url = database_url
        self.pool: Optional[SimpleConnectionPool] = None
        self.min_conn = min_conn
        self.max_conn = max_conn
        
    def initialize(self):
        """Initialize the connection pool"""
        try:
            self.pool = SimpleConnectionPool(
                self.min_conn,
                self.max_conn,
                self.database_url
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    def close(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for getting a database connection from the pool
        
        Yields:
            Database connection
        """
        conn = None
        try:
            if not self.pool:
                self.initialize()
            conn = self.pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                self.pool.putconn(conn)
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result rows as dictionaries
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                return [dict(row) for row in results]
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.rowcount
    
    def execute_insert_returning(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """
        Execute an INSERT query with RETURNING clause
        
        Args:
            query: SQL query string with RETURNING clause
            params: Query parameters
            
        Returns:
            Inserted row as dictionary
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                return dict(result) if result else None
    
    def insert_document(self, document_data: Dict[str, Any]) -> str:
        """
        Insert a document record
        
        Args:
            document_data: Document metadata
            
        Returns:
            Document ID
        """
        query = """
            INSERT INTO documents (
                document_id, file_name, file_type, upload_timestamp,
                file_size_bytes, page_count, storage_path, processing_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING document_id
        """
        params = (
            document_data['document_id'],
            document_data['file_name'],
            document_data['file_type'],
            document_data['upload_timestamp'],
            document_data['file_size_bytes'],
            document_data.get('page_count'),
            document_data['storage_path'],
            document_data.get('processing_status', 'pending')
        )
        result = self.execute_insert_returning(query, params)
        return result['document_id'] if result else None
    
    def insert_loan(self, loan_data: Dict[str, Any]) -> str:
        """
        Insert a loan record
        
        Args:
            loan_data: Normalized loan data
            
        Returns:
            Loan ID
        """
        query = """
            INSERT INTO loans (
                loan_id, document_id, loan_type, bank_name,
                principal_amount, interest_rate, tenure_months,
                extracted_data, extraction_confidence, extraction_timestamp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING loan_id
        """
        params = (
            loan_data['loan_id'],
            loan_data['document_id'],
            loan_data.get('loan_type'),
            loan_data.get('bank_name'),
            loan_data.get('principal_amount'),
            loan_data.get('interest_rate'),
            loan_data.get('tenure_months'),
            Json(loan_data.get('extracted_data', {})),
            loan_data.get('extraction_confidence'),
            loan_data.get('extraction_timestamp')
        )
        result = self.execute_insert_returning(query, params)
        return result['loan_id'] if result else None
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by ID
        
        Args:
            document_id: Document ID
            
        Returns:
            Document metadata or None
        """
        query = "SELECT * FROM documents WHERE document_id = %s"
        results = self.execute_query(query, (document_id,))
        return results[0] if results else None
    
    def get_loan(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a loan by ID
        
        Args:
            loan_id: Loan ID
            
        Returns:
            Loan data or None
        """
        query = "SELECT * FROM loans WHERE loan_id = %s"
        results = self.execute_query(query, (loan_id,))
        return results[0] if results else None
    
    def query_loans(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query loans with filters
        
        Args:
            filters: Query filters
            
        Returns:
            List of matching loans
        """
        query = "SELECT * FROM loans WHERE 1=1"
        params = []
        
        if filters.get('loan_type'):
            query += " AND loan_type = %s"
            params.append(filters['loan_type'])
        
        if filters.get('bank_name'):
            query += " AND bank_name ILIKE %s"
            params.append(f"%{filters['bank_name']}%")
        
        if filters.get('min_principal'):
            query += " AND principal_amount >= %s"
            params.append(filters['min_principal'])
        
        if filters.get('max_principal'):
            query += " AND principal_amount <= %s"
            params.append(filters['max_principal'])
        
        if filters.get('min_interest_rate'):
            query += " AND interest_rate >= %s"
            params.append(filters['min_interest_rate'])
        
        if filters.get('max_interest_rate'):
            query += " AND interest_rate <= %s"
            params.append(filters['max_interest_rate'])
        
        if filters.get('min_tenure_months'):
            query += " AND tenure_months >= %s"
            params.append(filters['min_tenure_months'])
        
        if filters.get('max_tenure_months'):
            query += " AND tenure_months <= %s"
            params.append(filters['max_tenure_months'])
        
        query += " ORDER BY created_at DESC"
        query += " LIMIT %s OFFSET %s"
        params.extend([filters.get('limit', 100), filters.get('offset', 0)])
        
        return self.execute_query(query, tuple(params))
    
    def update_document_status(self, document_id: str, status: str) -> int:
        """
        Update document processing status
        
        Args:
            document_id: Document ID
            status: New status
            
        Returns:
            Number of affected rows
        """
        query = "UPDATE documents SET processing_status = %s WHERE document_id = %s"
        return self.execute_update(query, (status, document_id))
    
    def create_processing_job(self, job_data: Dict[str, Any]) -> str:
        """
        Create a processing job record
        
        Args:
            job_data: Job data
            
        Returns:
            Job ID
        """
        query = """
            INSERT INTO processing_jobs (
                job_id, status, total_documents, processed_documents,
                failed_documents, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING job_id
        """
        params = (
            job_data['job_id'],
            job_data.get('status', 'queued'),
            job_data['total_documents'],
            job_data.get('processed_documents', 0),
            job_data.get('failed_documents', 0),
            job_data.get('created_at', datetime.now())
        )
        result = self.execute_insert_returning(query, params)
        return result['job_id'] if result else None
    
    def update_processing_job(self, job_id: str, updates: Dict[str, Any]) -> int:
        """
        Update a processing job
        
        Args:
            job_id: Job ID
            updates: Fields to update
            
        Returns:
            Number of affected rows
        """
        set_clauses = []
        params = []
        
        for key, value in updates.items():
            set_clauses.append(f"{key} = %s")
            params.append(value)
        
        params.append(job_id)
        query = f"UPDATE processing_jobs SET {', '.join(set_clauses)} WHERE job_id = %s"
        return self.execute_update(query, tuple(params))
    
    def get_processing_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a processing job by ID
        
        Args:
            job_id: Job ID
            
        Returns:
            Job data or None
        """
        query = "SELECT * FROM processing_jobs WHERE job_id = %s"
        results = self.execute_query(query, (job_id,))
        return results[0] if results else None
