"""
Object storage module for S3/MinIO integration
"""
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


class ObjectStorageManager:
    """Manages S3/MinIO object storage operations"""
    
    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        region: str = "us-east-1"
    ):
        """
        Initialize object storage manager
        
        Args:
            endpoint_url: S3/MinIO endpoint URL
            access_key: Access key ID
            secret_key: Secret access key
            bucket_name: Bucket name for storing documents
            region: AWS region
        """
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.region = region
        self.client = None
        
    def initialize(self):
        """Initialize S3 client and create bucket if it doesn't exist"""
        try:
            self.client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                config=Config(signature_version='s3v4')
            )
            
            # Create bucket if it doesn't exist
            try:
                self.client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"Bucket '{self.bucket_name}' already exists")
            except ClientError:
                self.client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Created bucket '{self.bucket_name}'")
                
        except Exception as e:
            logger.error(f"Failed to initialize object storage: {e}")
            raise
    
    def upload_file(self, file_data: bytes, object_key: str, metadata: dict = None) -> str:
        """
        Upload a file to object storage
        
        Args:
            file_data: File content as bytes
            object_key: Object key (path) in the bucket
            metadata: Optional metadata dictionary
            
        Returns:
            Object key of uploaded file
        """
        try:
            if not self.client:
                self.initialize()
            
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_data,
                **extra_args
            )
            
            logger.info(f"Uploaded file to {object_key}")
            return object_key
            
        except Exception as e:
            logger.error(f"Failed to upload file {object_key}: {e}")
            raise
    
    def download_file(self, object_key: str) -> bytes:
        """
        Download a file from object storage
        
        Args:
            object_key: Object key (path) in the bucket
            
        Returns:
            File content as bytes
        """
        try:
            if not self.client:
                self.initialize()
            
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            file_data = response['Body'].read()
            logger.info(f"Downloaded file from {object_key}")
            return file_data
            
        except Exception as e:
            logger.error(f"Failed to download file {object_key}: {e}")
            raise
    
    def delete_file(self, object_key: str) -> bool:
        """
        Delete a file from object storage
        
        Args:
            object_key: Object key (path) in the bucket
            
        Returns:
            True if successful
        """
        try:
            if not self.client:
                self.initialize()
            
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            logger.info(f"Deleted file {object_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file {object_key}: {e}")
            raise
    
    def file_exists(self, object_key: str) -> bool:
        """
        Check if a file exists in object storage
        
        Args:
            object_key: Object key (path) in the bucket
            
        Returns:
            True if file exists
        """
        try:
            if not self.client:
                self.initialize()
            
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
            
        except ClientError:
            return False
        except Exception as e:
            logger.error(f"Error checking file existence {object_key}: {e}")
            raise
    
    def get_file_metadata(self, object_key: str) -> dict:
        """
        Get metadata for a file
        
        Args:
            object_key: Object key (path) in the bucket
            
        Returns:
            Metadata dictionary
        """
        try:
            if not self.client:
                self.initialize()
            
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            return {
                'content_length': response.get('ContentLength'),
                'content_type': response.get('ContentType'),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {})
            }
            
        except Exception as e:
            logger.error(f"Failed to get metadata for {object_key}: {e}")
            raise
    
    def list_files(self, prefix: str = "") -> list:
        """
        List files in the bucket with optional prefix
        
        Args:
            prefix: Optional prefix to filter files
            
        Returns:
            List of object keys
        """
        try:
            if not self.client:
                self.initialize()
            
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            return [obj['Key'] for obj in response['Contents']]
            
        except Exception as e:
            logger.error(f"Failed to list files with prefix {prefix}: {e}")
            raise
    
    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for temporary access to a file
        
        Args:
            object_key: Object key (path) in the bucket
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL
        """
        try:
            if not self.client:
                self.initialize()
            
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated presigned URL for {object_key}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {object_key}: {e}")
            raise
