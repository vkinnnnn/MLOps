"""
Batch processing handler for processing multiple loan documents.

This module provides functionality to process multiple documents sequentially,
handle failures gracefully, and generate summary reports.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import traceback

from src.api.document_ingestion import DocumentUploadHandler, DocumentMetadata, ValidationError
from storage.storage_service import StorageService


logger = logging.getLogger(__name__)


class BatchProcessingResult:
    """Result of processing a single document in a batch."""
    
    def __init__(
        self,
        file_name: str,
        status: str,
        document_id: Optional[str] = None,
        loan_id: Optional[str] = None,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        processing_time: Optional[float] = None
    ):
        """
        Initialize batch processing result.
        
        Args:
            file_name: Name of the processed file
            status: Processing status (success, failed, skipped)
            document_id: Document ID if successfully uploaded
            loan_id: Loan ID if successfully extracted
            error_message: Error message if processing failed
            error_type: Type of error (validation, extraction, storage, etc.)
            processing_time: Time taken to process in seconds
        """
        self.file_name = file_name
        self.status = status
        self.document_id = document_id
        self.loan_id = loan_id
        self.error_message = error_message
        self.error_type = error_type
        self.processing_time = processing_time
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'file_name': self.file_name,
            'status': self.status,
            'document_id': self.document_id,
            'loan_id': self.loan_id,
            'error_message': self.error_message,
            'error_type': self.error_type,
            'processing_time': self.processing_time,
            'timestamp': self.timestamp.isoformat()
        }


class BatchProcessingSummary:
    """Summary report for batch processing operation."""
    
    def __init__(self, job_id: str, total_documents: int):
        """
        Initialize batch processing summary.
        
        Args:
            job_id: Unique identifier for the batch job
            total_documents: Total number of documents to process
        """
        self.job_id = job_id
        self.total_documents = total_documents
        self.processed_documents = 0
        self.successful_documents = 0
        self.failed_documents = 0
        self.results: List[BatchProcessingResult] = []
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
    
    def add_result(self, result: BatchProcessingResult):
        """Add a processing result to the summary."""
        self.results.append(result)
        self.processed_documents += 1
        
        if result.status == 'success':
            self.successful_documents += 1
        elif result.status == 'failed':
            self.failed_documents += 1
    
    def finalize(self):
        """Finalize the summary after all processing is complete."""
        self.end_time = datetime.now()
    
    def get_total_processing_time(self) -> float:
        """Get total processing time in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary."""
        return {
            'job_id': self.job_id,
            'total_documents': self.total_documents,
            'processed_documents': self.processed_documents,
            'successful_documents': self.successful_documents,
            'failed_documents': self.failed_documents,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_processing_time': self.get_total_processing_time(),
            'results': [result.to_dict() for result in self.results]
        }


class BatchProcessingHandler:
    """
    Handler for batch processing of multiple loan documents.
    
    Processes documents sequentially, handles failures gracefully,
    and generates comprehensive summary reports.
    """
    
    def __init__(
        self,
        upload_handler: Optional[DocumentUploadHandler] = None,
        storage_service: Optional[StorageService] = None
    ):
        """
        Initialize batch processing handler.
        
        Args:
            upload_handler: Document upload handler
            storage_service: Storage service
        """
        self.upload_handler = upload_handler or DocumentUploadHandler()
        self.storage_service = storage_service or StorageService()
    
    def process_batch_from_paths(
        self,
        file_paths: List[str],
        continue_on_failure: bool = True
    ) -> BatchProcessingSummary:
        """
        Process multiple documents from file paths.
        
        Args:
            file_paths: List of file paths to process
            continue_on_failure: Whether to continue processing if a document fails
        
        Returns:
            BatchProcessingSummary with processing results
        """
        # Create processing job in database
        job_id = self.storage_service.create_processing_job(len(file_paths))
        
        logger.info(f"Starting batch processing job {job_id} with {len(file_paths)} documents")
        
        # Initialize summary
        summary = BatchProcessingSummary(job_id, len(file_paths))
        
        # Update job status to processing
        self.storage_service.update_processing_job(job_id, status='processing')
        
        # Process each document sequentially
        for file_path in file_paths:
            file_name = Path(file_path).name
            logger.info(f"Processing document: {file_name}")
            
            try:
                result = self._process_single_document(file_path)
                summary.add_result(result)
                
                # Update job progress
                self.storage_service.update_processing_job(
                    job_id,
                    processed_documents=summary.processed_documents,
                    failed_documents=summary.failed_documents
                )
                
                logger.info(f"Document {file_name} processed: {result.status}")
                
            except Exception as e:
                # Log error with diagnostic information
                error_msg = str(e)
                error_trace = traceback.format_exc()
                logger.error(f"Unexpected error processing {file_name}: {error_msg}")
                logger.debug(f"Error traceback:\n{error_trace}")
                
                # Create failed result
                result = BatchProcessingResult(
                    file_name=file_name,
                    status='failed',
                    error_message=error_msg,
                    error_type='unexpected_error'
                )
                summary.add_result(result)
                
                # Update job progress
                self.storage_service.update_processing_job(
                    job_id,
                    processed_documents=summary.processed_documents,
                    failed_documents=summary.failed_documents
                )
                
                # Stop processing if continue_on_failure is False
                if not continue_on_failure:
                    logger.warning("Stopping batch processing due to failure")
                    break
        
        # Finalize summary
        summary.finalize()
        
        # Update job as completed
        final_status = 'completed' if summary.failed_documents == 0 else 'completed_with_errors'
        self.storage_service.update_processing_job(
            job_id,
            status=final_status,
            completed=True
        )
        
        logger.info(
            f"Batch processing job {job_id} completed: "
            f"{summary.successful_documents} successful, "
            f"{summary.failed_documents} failed"
        )
        
        return summary
    
    def process_batch_from_bytes(
        self,
        documents: List[Dict[str, Any]],
        continue_on_failure: bool = True
    ) -> BatchProcessingSummary:
        """
        Process multiple documents from byte data.
        
        Args:
            documents: List of dictionaries with 'file_name' and 'file_data' keys
            continue_on_failure: Whether to continue processing if a document fails
        
        Returns:
            BatchProcessingSummary with processing results
        """
        # Create processing job in database
        job_id = self.storage_service.create_processing_job(len(documents))
        
        logger.info(f"Starting batch processing job {job_id} with {len(documents)} documents")
        
        # Initialize summary
        summary = BatchProcessingSummary(job_id, len(documents))
        
        # Update job status to processing
        self.storage_service.update_processing_job(job_id, status='processing')
        
        # Process each document sequentially
        for doc in documents:
            file_name = doc.get('file_name', 'unknown')
            file_data = doc.get('file_data')
            
            logger.info(f"Processing document: {file_name}")
            
            if not file_data:
                result = BatchProcessingResult(
                    file_name=file_name,
                    status='failed',
                    error_message='No file data provided',
                    error_type='validation_error'
                )
                summary.add_result(result)
                continue
            
            try:
                result = self._process_single_document_from_bytes(file_name, file_data)
                summary.add_result(result)
                
                # Update job progress
                self.storage_service.update_processing_job(
                    job_id,
                    processed_documents=summary.processed_documents,
                    failed_documents=summary.failed_documents
                )
                
                logger.info(f"Document {file_name} processed: {result.status}")
                
            except Exception as e:
                # Log error with diagnostic information
                error_msg = str(e)
                error_trace = traceback.format_exc()
                logger.error(f"Unexpected error processing {file_name}: {error_msg}")
                logger.debug(f"Error traceback:\n{error_trace}")
                
                # Create failed result
                result = BatchProcessingResult(
                    file_name=file_name,
                    status='failed',
                    error_message=error_msg,
                    error_type='unexpected_error'
                )
                summary.add_result(result)
                
                # Update job progress
                self.storage_service.update_processing_job(
                    job_id,
                    processed_documents=summary.processed_documents,
                    failed_documents=summary.failed_documents
                )
                
                # Stop processing if continue_on_failure is False
                if not continue_on_failure:
                    logger.warning("Stopping batch processing due to failure")
                    break
        
        # Finalize summary
        summary.finalize()
        
        # Update job as completed
        final_status = 'completed' if summary.failed_documents == 0 else 'completed_with_errors'
        self.storage_service.update_processing_job(
            job_id,
            status=final_status,
            completed=True
        )
        
        logger.info(
            f"Batch processing job {job_id} completed: "
            f"{summary.successful_documents} successful, "
            f"{summary.failed_documents} failed"
        )
        
        return summary
    
    def _process_single_document(self, file_path: str) -> BatchProcessingResult:
        """
        Process a single document from file path.
        
        Args:
            file_path: Path to the document file
        
        Returns:
            BatchProcessingResult for this document
        """
        file_name = Path(file_path).name
        start_time = datetime.now()
        
        try:
            # Step 1: Upload and validate document
            logger.debug(f"Uploading document: {file_name}")
            metadata = self.upload_handler.upload_document_from_path(file_path)
            document_id = metadata.document_id
            
            # Step 2: Store document in storage service
            logger.debug(f"Storing document {document_id} in storage")
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            storage_result = self.storage_service.store_document(
                file_data=file_data,
                file_name=file_name,
                file_type=metadata.file_type,
                page_count=metadata.page_count
            )
            
            # Update document status to completed
            self.storage_service.update_document_status(document_id, 'completed')
            
            # Note: Extraction and normalization would happen here in full implementation
            loan_id = None
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create success result
            return BatchProcessingResult(
                file_name=file_name,
                status='success',
                document_id=document_id,
                loan_id=loan_id,
                processing_time=processing_time
            )
            
        except ValidationError as e:
            # Handle validation errors
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.warning(f"Validation error for {file_name}: {str(e)}")
            
            return BatchProcessingResult(
                file_name=file_name,
                status='failed',
                error_message=str(e),
                error_type='validation_error',
                processing_time=processing_time
            )
            
        except Exception as e:
            # Handle other errors
            processing_time = (datetime.now() - start_time).total_seconds()
            error_trace = traceback.format_exc()
            logger.error(f"Error processing {file_name}: {str(e)}")
            logger.debug(f"Error traceback:\n{error_trace}")
            
            return BatchProcessingResult(
                file_name=file_name,
                status='failed',
                error_message=str(e),
                error_type='processing_error',
                processing_time=processing_time
            )
    
    def _process_single_document_from_bytes(
        self,
        file_name: str,
        file_data: bytes
    ) -> BatchProcessingResult:
        """
        Process a single document from byte data.
        
        Args:
            file_name: Name of the file
            file_data: File content as bytes
        
        Returns:
            BatchProcessingResult for this document
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Upload and validate document
            logger.debug(f"Uploading document: {file_name}")
            metadata = self.upload_handler.upload_document(file_data, file_name)
            document_id = metadata.document_id
            
            # Step 2: Store document in storage service
            logger.debug(f"Storing document {document_id} in storage")
            storage_result = self.storage_service.store_document(
                file_data=file_data,
                file_name=file_name,
                file_type=metadata.file_type,
                page_count=metadata.page_count
            )
            
            # Update document status to completed
            self.storage_service.update_document_status(document_id, 'completed')
            
            # Note: Extraction and normalization would happen here in full implementation
            loan_id = None
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create success result
            return BatchProcessingResult(
                file_name=file_name,
                status='success',
                document_id=document_id,
                loan_id=loan_id,
                processing_time=processing_time
            )
            
        except ValidationError as e:
            # Handle validation errors
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.warning(f"Validation error for {file_name}: {str(e)}")
            
            return BatchProcessingResult(
                file_name=file_name,
                status='failed',
                error_message=str(e),
                error_type='validation_error',
                processing_time=processing_time
            )
            
        except Exception as e:
            # Handle other errors
            processing_time = (datetime.now() - start_time).total_seconds()
            error_trace = traceback.format_exc()
            logger.error(f"Error processing {file_name}: {str(e)}")
            logger.debug(f"Error traceback:\n{error_trace}")
            
            return BatchProcessingResult(
                file_name=file_name,
                status='failed',
                error_message=str(e),
                error_type='processing_error',
                processing_time=processing_time
            )
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a batch processing job.
        
        Args:
            job_id: Job UUID
        
        Returns:
            Dictionary with job status or None if not found
        """
        return self.storage_service.get_processing_job(job_id)
