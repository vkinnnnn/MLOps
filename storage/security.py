"""
Security measures for data protection including encryption and access control.
"""
import os
import hashlib
import secrets
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend


class UserRole(str, Enum):
    """User roles for role-based access control."""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class EncryptionManager:
    """Manages encryption at rest for sensitive data."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption manager.
        
        Args:
            encryption_key: Base64-encoded encryption key. If None, generates or reads from env.
        """
        if encryption_key:
            self.key = encryption_key.encode()
        else:
            # Try to get from environment or generate new
            env_key = os.getenv('ENCRYPTION_KEY')
            if env_key:
                self.key = env_key.encode()
            else:
                # Generate new key (should be stored securely in production)
                self.key = Fernet.generate_key()
        
        self.cipher = Fernet(self.key)
    
    def encrypt_data(self, data: bytes) -> bytes:
        """
        Encrypt data using Fernet (AES-128 in CBC mode).
        
        Args:
            data: Data to encrypt as bytes
        
        Returns:
            Encrypted data as bytes
        """
        return self.cipher.encrypt(data)
    
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Encrypted data as bytes
        
        Returns:
            Decrypted data as bytes
        """
        return self.cipher.decrypt(encrypted_data)
    
    def encrypt_string(self, text: str) -> str:
        """
        Encrypt a string and return base64-encoded result.
        
        Args:
            text: Text to encrypt
        
        Returns:
            Base64-encoded encrypted string
        """
        encrypted = self.cipher.encrypt(text.encode())
        return encrypted.decode()
    
    def decrypt_string(self, encrypted_text: str) -> str:
        """
        Decrypt a base64-encoded encrypted string.
        
        Args:
            encrypted_text: Base64-encoded encrypted string
        
        Returns:
            Decrypted text
        """
        decrypted = self.cipher.decrypt(encrypted_text.encode())
        return decrypted.decode()
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new encryption key.
        
        Returns:
            Base64-encoded encryption key
        """
        return Fernet.generate_key().decode()
    
    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> tuple:
        """
        Hash a password using PBKDF2.
        
        Args:
            password: Password to hash
            salt: Salt for hashing. If None, generates new salt.
        
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = os.urandom(32)
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        hashed = kdf.derive(password.encode())
        return hashed, salt
    
    @staticmethod
    def verify_password(password: str, hashed_password: bytes, salt: bytes) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Password to verify
            hashed_password: Hashed password
            salt: Salt used for hashing
        
        Returns:
            True if password matches, False otherwise
        """
        new_hash, _ = EncryptionManager.hash_password(password, salt)
        return new_hash == hashed_password


class AccessControlManager:
    """Manages role-based access control (RBAC)."""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize access control manager.
        
        Args:
            secret_key: Secret key for JWT signing. If None, reads from env or generates.
        """
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32))
        self.algorithm = 'HS256'
        self.token_expiration_hours = 24
    
    def create_access_token(
        self,
        user_id: str,
        role: UserRole,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            user_id: User identifier
            role: User role
            additional_claims: Additional claims to include in token
        
        Returns:
            JWT token string
        """
        expiration = datetime.utcnow() + timedelta(hours=self.token_expiration_hours)
        
        payload = {
            'user_id': user_id,
            'role': role.value,
            'exp': expiration,
            'iat': datetime.utcnow()
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def check_permission(
        self,
        token: str,
        required_role: UserRole,
        resource_owner_id: Optional[str] = None
    ) -> bool:
        """
        Check if token has permission for an action.
        
        Args:
            token: JWT token string
            required_role: Minimum required role
            resource_owner_id: Owner ID of the resource (for user-level access)
        
        Returns:
            True if permission granted, False otherwise
        """
        payload = self.verify_token(token)
        
        if not payload:
            return False
        
        user_role = UserRole(payload.get('role'))
        user_id = payload.get('user_id')
        
        # Admin has access to everything
        if user_role == UserRole.ADMIN:
            return True
        
        # Check role hierarchy
        role_hierarchy = {
            UserRole.ADMIN: 3,
            UserRole.USER: 2,
            UserRole.VIEWER: 1
        }
        
        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
            return False
        
        # Check resource ownership if specified
        if resource_owner_id and user_id != resource_owner_id:
            return False
        
        return True
    
    def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Extract user information from token.
        
        Args:
            token: JWT token string
        
        Returns:
            Dictionary with user_id and role, or None if invalid
        """
        payload = self.verify_token(token)
        
        if not payload:
            return None
        
        return {
            'user_id': payload.get('user_id'),
            'role': payload.get('role')
        }


class TLSConfig:
    """Configuration for TLS/SSL encryption in transit."""
    
    @staticmethod
    def get_ssl_context_config() -> Dict[str, Any]:
        """
        Get SSL context configuration for secure connections.
        
        Returns:
            Dictionary with SSL configuration
        """
        return {
            'ssl_cert_file': os.getenv('SSL_CERT_FILE', '/etc/ssl/certs/server.crt'),
            'ssl_key_file': os.getenv('SSL_KEY_FILE', '/etc/ssl/private/server.key'),
            'ssl_ca_file': os.getenv('SSL_CA_FILE', '/etc/ssl/certs/ca.crt'),
            'ssl_verify_mode': 'CERT_REQUIRED',
            'ssl_minimum_version': 'TLSv1_3'
        }
    
    @staticmethod
    def get_database_ssl_config() -> Dict[str, str]:
        """
        Get SSL configuration for database connections.
        
        Returns:
            Dictionary with database SSL parameters
        """
        return {
            'sslmode': 'require',
            'sslrootcert': os.getenv('DB_SSL_ROOT_CERT', '/etc/ssl/certs/ca.crt'),
            'sslcert': os.getenv('DB_SSL_CERT', '/etc/ssl/certs/client.crt'),
            'sslkey': os.getenv('DB_SSL_KEY', '/etc/ssl/private/client.key')
        }
    
    @staticmethod
    def get_s3_ssl_config() -> Dict[str, Any]:
        """
        Get SSL configuration for S3/MinIO connections.
        
        Returns:
            Dictionary with S3 SSL parameters
        """
        return {
            'use_ssl': True,
            'verify': os.getenv('S3_SSL_VERIFY', 'true').lower() == 'true',
            'cert': os.getenv('S3_SSL_CERT')
        }


class AuditLogger:
    """Logs security-relevant events for compliance and monitoring."""
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize audit logger.
        
        Args:
            log_file: Path to audit log file. If None, uses default.
        """
        self.log_file = log_file or os.getenv('AUDIT_LOG_FILE', '/var/log/loan-extractor/audit.log')
    
    def log_access(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        success: bool,
        ip_address: Optional[str] = None
    ):
        """
        Log an access event.
        
        Args:
            user_id: User performing the action
            action: Action performed (read, write, delete, etc.)
            resource_type: Type of resource (document, loan, etc.)
            resource_id: ID of the resource
            success: Whether action was successful
            ip_address: IP address of the request
        """
        timestamp = datetime.utcnow().isoformat()
        
        log_entry = {
            'timestamp': timestamp,
            'user_id': user_id,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'success': success,
            'ip_address': ip_address
        }
        
        # In production, this should write to a secure log file or logging service
        print(f"AUDIT: {log_entry}")
    
    def log_authentication(
        self,
        user_id: str,
        success: bool,
        ip_address: Optional[str] = None,
        failure_reason: Optional[str] = None
    ):
        """
        Log an authentication event.
        
        Args:
            user_id: User attempting authentication
            success: Whether authentication was successful
            ip_address: IP address of the request
            failure_reason: Reason for failure if applicable
        """
        timestamp = datetime.utcnow().isoformat()
        
        log_entry = {
            'timestamp': timestamp,
            'event_type': 'authentication',
            'user_id': user_id,
            'success': success,
            'ip_address': ip_address,
            'failure_reason': failure_reason
        }
        
        print(f"AUDIT: {log_entry}")


# Global instances
_encryption_manager: Optional[EncryptionManager] = None
_access_control_manager: Optional[AccessControlManager] = None
_audit_logger: Optional[AuditLogger] = None


def get_encryption_manager() -> EncryptionManager:
    """Get or create the global encryption manager instance."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


def get_access_control_manager() -> AccessControlManager:
    """Get or create the global access control manager instance."""
    global _access_control_manager
    if _access_control_manager is None:
        _access_control_manager = AccessControlManager()
    return _access_control_manager


def get_audit_logger() -> AuditLogger:
    """Get or create the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
