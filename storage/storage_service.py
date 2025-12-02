"""
Storage service for managing documents and extracted loan data.

This module provides a unified interface for storing and retrieving
documents, loan data, and processing job information.
"""

import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class StorageService:
    """
    Unified storage service for documents and loan data.
    
    Provides in-memory storage for demo purposes.
    In production, this would integrate with PostgreSQL and S3/MinIO.
    """
    
    def __init__(self):
        """Initialize storage service."""
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.loans: Dict[str, Dict[str, Any]] = {}
        self.processing_jobs: Dict[str, Dict[str, Any]] = {}
        self.extractions: Dict[str, Dict[str, Any]] = {}
        logger.info("StorageService initialized (in-memory mode)")
    
    # ========================================================================
    # Document Storage
    # ========================================================================
    
    def store_document(
        self,
        file_data: bytes,
        file_name: str,
        file_type: str,
        page_count: int,
        document_id: Optional[str] = None
    ) -> str:
        """
        Store a document.
        
        Args:
            file_data: Binary file content
            file_name: Name of the file
            file_type: MIME type
            page_count: Number of pages
            document_id: Optional document ID (generated if not provided)
        
        Returns:
            Document ID
        """
        try:
            if not document_id:
                document_id = str(uuid.uuid4())
            
            logger.info(f"Storing document: {document_id}")
            
            # Store document metadata
            self.documents[document_id] = {
                'document_id': document_id,
                'file_name': file_name,
                'file_type': file_type,
                'file_size_bytes': len(file_data),
                'page_count': page_count,
                'storage_path': f'/documents/{document_id}',
                'upload_timestamp': datetime.now().isoformat(),
                'processing_status': 'pending',
                'file_data': file_data  # In production, store in S3/MinIO
            }
            
            logger.info(f"Document stored: {document_id}")
            
            return document_id
            
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")
            raise

    def store_extraction_result(
        self,
        document_id: str,
        extraction_result: Dict[str, Any]
    ) -> None:
        """
        Attach extraction payload to a stored document.
        """
        if document_id not in self.documents:
            raise ValueError(f"Document not found: {document_id}")

        self.extractions[document_id] = extraction_result

        merged_text = extraction_result.get("complete_text", {}).get("merged_text", "")
        accuracy = extraction_result.get("accuracy_metrics", {}).get("overall_accuracy")

        document_entry = self.documents[document_id]
        document_entry["extracted_data"] = extraction_result
        document_entry["extracted_text"] = merged_text
        if accuracy is not None:
            document_entry["accuracy"] = accuracy
        if "processing_status" in document_entry:
            document_entry["processing_status"] = "completed"
    
    def retrieve_document(self, document_id: str) -> Optional[bytes]:
        """
        Retrieve document file data.
        
        Args:
            document_id: Document identifier
        
        Returns:
            Binary file content or None if not found
        """
        try:
            if document_id not in self.documents:
                logger.warning(f"Document not found: {document_id}")
                return None
            
            return self.documents[document_id].get('file_data')
            
        except Exception as e:
            logger.error(f"Error retrieving document: {str(e)}")
            return None
    
    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document metadata.
        
        Args:
            document_id: Document identifier
        
        Returns:
            Document metadata dictionary or None if not found
        """
        try:
            if document_id not in self.documents:
                return None
            
            # Return metadata without file data
            metadata = self.documents[document_id].copy()
            metadata.pop('file_data', None)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting document metadata: {str(e)}")
            return None
    
    def update_document_status(
        self,
        document_id: str,
        status: str
    ) -> bool:
        """
        Update document processing status.
        
        Args:
            document_id: Document identifier
            status: New status (pending, processing, completed, failed)
        
        Returns:
            True if updated, False otherwise
        """
        try:
            if document_id not in self.documents:
                logger.warning(f"Document not found: {document_id}")
                return False
            
            self.documents[document_id]['processing_status'] = status
            logger.info(f"Document status updated: {document_id} -> {status}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating document status: {str(e)}")
            return False
    
    # ========================================================================
    # Loan Data Storage
    # ========================================================================
    
    def store_extracted_data(
        self,
        document_id: str,
        loan_type: str,
        extracted_data: Dict[str, Any],
        bank_name: Optional[str] = None,
        principal_amount: Optional[float] = None,
        interest_rate: Optional[float] = None,
        tenure_months: Optional[int] = None,
        extraction_confidence: float = 0.0,
        loan_id: Optional[str] = None
    ) -> str:
        """
        Store extracted loan data.
        
        Args:
            document_id: Associated document ID
            loan_type: Type of loan
            extracted_data: Complete extracted data dictionary
            bank_name: Name of lending institution
            principal_amount: Loan principal
            interest_rate: Interest rate
            tenure_months: Loan tenure
            extraction_confidence: Confidence score
            loan_id: Optional loan ID (generated if not provided)
        
        Returns:
            Loan ID
        """
        try:
            if not loan_id:
                loan_id = str(uuid.uuid4())
            
            logger.info(f"Storing extracted data: {loan_id}")
            
            # Store loan data
            self.loans[loan_id] = {
                'loan_id': loan_id,
                'document_id': document_id,
                'loan_type': loan_type,
                'bank_name': bank_name,
                'principal_amount': principal_amount,
                'interest_rate': interest_rate,
                'tenure_months': tenure_months,
                'extraction_confidence': extraction_confidence,
                'extracted_data': extracted_data,
                'extraction_timestamp': datetime.now().isoformat()
            }
            
            # Update document status
            self.update_document_status(document_id, 'completed')
            
            logger.info(f"Extracted data stored: {loan_id}")
            
            return loan_id
            
        except Exception as e:
            logger.error(f"Error storing extracted data: {str(e)}")
            raise
    
    def get_loan_data(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve loan data by ID.
        
        Args:
            loan_id: Loan identifier
        
        Returns:
            Loan data dictionary or None if not found
        """
        try:
            return self.loans.get(loan_id)
            
        except Exception as e:
            logger.error(f"Error retrieving loan data: {str(e)}")
            return None
    
    def query_loans(
        self,
        loan_type: Optional[str] = None,
        bank_name: Optional[str] = None,
        min_principal: Optional[float] = None,
        max_principal: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query loans with filters.
        
        Args:
            loan_type: Filter by loan type
            bank_name: Filter by bank name
            min_principal: Minimum principal amount
            max_principal: Maximum principal amount
            limit: Maximum number of results
        
        Returns:
            List of loan data dictionaries
        """
        try:
            results = []
            
            for loan_id, loan_data in self.loans.items():
                # Apply filters
                if loan_type and loan_data.get('loan_type') != loan_type:
                    continue
                
                if bank_name and loan_data.get('bank_name') != bank_name:
                    continue
                
                if min_principal and (not loan_data.get('principal_amount') or loan_data['principal_amount'] < min_principal):
                    continue
                
                if max_principal and (not loan_data.get('principal_amount') or loan_data['principal_amount'] > max_principal):
                    continue
                
                results.append(loan_data)
                
                if len(results) >= limit:
                    break
            
            logger.info(f"Query returned {len(results)} loans")
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying loans: {str(e)}")
            return []
    
    # ========================================================================
    # Processing Job Management
    # ========================================================================
    
    def create_processing_job(
        self,
        total_documents: int,
        job_id: Optional[str] = None
    ) -> str:
        """
        Create a batch processing job.
        
        Args:
            total_documents: Total number of documents to process
            job_id: Optional job ID (generated if not provided)
        
        Returns:
            Job ID
        """
        try:
            if not job_id:
                job_id = str(uuid.uuid4())
            
            logger.info(f"Creating processing job: {job_id}")
            
            self.processing_jobs[job_id] = {
                'job_id': job_id,
                'status': 'queued',
                'total_documents': total_documents,
                'processed_documents': 0,
                'failed_documents': 0,
                'created_at': datetime.now().isoformat(),
                'completed_at': None
            }
            
            logger.info(f"Processing job created: {job_id}")
            
            return job_id
            
        except Exception as e:
            logger.error(f"Error creating processing job: {str(e)}")
            raise
    
    def update_processing_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        processed_documents: Optional[int] = None,
        failed_documents: Optional[int] = None,
        completed: bool = False
    ) -> bool:
        """
        Update processing job status.
        
        Args:
            job_id: Job identifier
            status: New status
            processed_documents: Number of processed documents
            failed_documents: Number of failed documents
            completed: Whether job is completed
        
        Returns:
            True if updated, False otherwise
        """
        try:
            if job_id not in self.processing_jobs:
                logger.warning(f"Processing job not found: {job_id}")
                return False
            
            job = self.processing_jobs[job_id]
            
            if status:
                job['status'] = status
            
            if processed_documents is not None:
                job['processed_documents'] = processed_documents
            
            if failed_documents is not None:
                job['failed_documents'] = failed_documents
            
            if completed:
                job['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"Processing job updated: {job_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating processing job: {str(e)}")
            return False
    
    def get_processing_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get processing job status.
        
        Args:
            job_id: Job identifier
        
        Returns:
            Job data dictionary or None if not found
        """
        try:
            return self.processing_jobs.get(job_id)
            
        except Exception as e:
            logger.error(f"Error retrieving processing job: {str(e)}")
            return None
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        return {
            'total_documents': len(self.documents),
            'total_loans': len(self.loans),
            'total_jobs': len(self.processing_jobs),
            'pending_documents': sum(1 for d in self.documents.values() if d['processing_status'] == 'pending'),
            'completed_documents': sum(1 for d in self.documents.values() if d['processing_status'] == 'completed'),
            'failed_documents': sum(1 for d in self.documents.values() if d['processing_status'] == 'failed')
        }

    def get_extraction_result(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored extraction result for a document.
        """
        return self.extractions.get(document_id)

    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents with extraction context when available.
        """
        documents: List[Dict[str, Any]] = []
        for doc_id, metadata in self.documents.items():
            entry = metadata.copy()
            entry.pop('file_data', None)

            extraction = self.extractions.get(doc_id)
            if extraction:
                entry['extracted_data'] = extraction
                entry['extracted_text'] = extraction.get("complete_text", {}).get("merged_text", "")
                entry['accuracy_metrics'] = extraction.get("accuracy_metrics")
                entry['accuracy'] = extraction.get("accuracy_metrics", {}).get("overall_accuracy")

            documents.append(entry)

        documents.sort(key=lambda item: item.get('upload_timestamp', ''), reverse=True)
        return documents
