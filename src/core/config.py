"""
Configuration management for the Student Loan Intelligence System.

Following KIRO Global Steering Guidelines for secure configuration handling.
"""

import os
from typing import Optional, List
from pathlib import Path

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore additional env vars
    )
    
    # ===================================
    # Application Basic Configuration
    # ===================================
    app_name: str = Field(
        default="Student Loan Intelligence",
        description="Application name"
    )
    
    environment: str = Field(
        default="development",
        description="Deployment environment"
    )
    
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    host: str = Field(
        default="0.0.0.0",
        description="Server host address"
    )
    
    port: int = Field(
        default=8000,
        description="Server port"
    )
    
    # ===================================
    # API Keys - REQUIRED
    # ===================================
    anthropic_api_key: str = Field(
        ...,
        description="Anthropic Claude API key",
        min_length=1
    )
    
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    
    # ===================================
    # Database Configuration
    # ===================================
    database_url: Optional[str] = Field(
        default=None,
        description="Database connection URL"
    )
    
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL"
    )
    
    test_database_url: Optional[str] = Field(
        default="sqlite:///test_student_loan_intelligence.db",
        description="Test database URL"
    )
    
    # ===================================
    # AI/Model Configuration
    # ===================================
    default_model: str = Field(
        default="claude-3-sonnet-20241022",
        description="Default AI model"
    )
    
    max_tokens: int = Field(
        default=4096,
        description="Maximum tokens for AI responses",
        ge=1,
        le=16384
    )
    
    temperature: float = Field(
        default=0.7,
        description="AI model temperature",
        ge=0.0,
        le=2.0
    )
    
    openai_model: str = Field(
        default="gpt-4-turbo",
        description="OpenAI model name"
    )
    
    # ===================================
    # Security Configuration
    # ===================================
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT secret key",
        min_length=32
    )
    
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    
    jwt_expiration_hours: int = Field(
        default=24,
        description="JWT token expiration in hours",
        ge=1
    )
    
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"],
        description="CORS allowed origins"
    )
    
    # ===================================
    # File Processing Configuration
    # ===================================
    max_file_size: int = Field(
        default=50 * 1024 * 1024,  # 50MB in bytes
        description="Maximum file upload size in bytes",
        ge=1
    )
    
    supported_formats: List[str] = Field(
        default_factory=lambda: ["pdf", "docx", "jpg", "jpeg", "png", "tiff", "bmp"],
        description="Supported file formats"
    )
    
    processing_timeout: int = Field(
        default=300,  # 5 minutes
        description="Document processing timeout in seconds",
        ge=1
    )
    
    ocr_engine: str = Field(
        default="auto",
        description="OCR engine to use (tesseract, easyocr, auto)"
    )
    
    # ===================================
    # Performance Configuration
    # ===================================
    max_concurrent_requests: int = Field(
        default=100,
        description="Maximum concurrent requests",
        ge=1
    )
    
    request_timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
        ge=1
    )
    
    cache_ttl: int = Field(
        default=3600,  # 1 hour
        description="Cache TTL in seconds",
        ge=1
    )
    
    max_workers: int = Field(
        default=4,
        description="Maximum worker processes",
        ge=1
    )
    
    # ===================================
    # Monitoring Configuration
    # ===================================
    prometheus_enabled: bool = Field(
        default=True,
        description="Enable Prometheus metrics"
    )
    
    prometheus_port: int = Field(
        default=9090,
        description="Prometheus metrics port",
        ge=1
    )
    
    log_file_path: str = Field(
        default="logs/student_loan_intelligence.log",
        description="Log file path"
    )
    
    enable_request_logging: bool = Field(
        default=True,
        description="Enable request logging"
    )
    
    # ===================================
    # External Services Configuration
    # ===================================
    aws_s3_bucket: Optional[str] = Field(
        default=None,
        description="AWS S3 bucket name"
    )
    
    aws_region: str = Field(
        default="us-east-1",
        description="AWS region"
    )
    
    aws_access_key_id: Optional[str] = Field(
        default=None,
        description="AWS access key"
    )
    
    aws_secret_access_key: Optional[str] = Field(
        default=None,
        description="AWS secret key"
    )
    
    # Email configuration (optional)
    smtp_host: Optional[str] = Field(
        default=None,
        description="SMTP server host"
    )
    
    smtp_port: Optional[int] = Field(
        default=None,
        description="SMTP server port"
    )
    
    smtp_user: Optional[str] = Field(
        default=None,
        description="SMTP username"
    )
    
    smtp_password: Optional[str] = Field(
        default=None,
        description="SMTP password"
    )
    
    smtp_tls: bool = Field(
        default=True,
        description="Enable SMTP TLS"
    )
    
    # ===================================
    # Feature Flags
    # ===================================
    enable_dev_middleware: bool = Field(
        default=False,
        description="Enable development middleware"
    )
    
    hot_reload: bool = Field(
        default=False,
        description="Enable hot reload in development"
    )
    
    enable_beta_features: bool = Field(
        default=False,
        description="Enable beta features"
    )
    
    enable_experimental_features: bool = Field(
        default=False,
        description="Enable experimental features"
    )
    
    enable_analytics: bool = Field(
        default=True,
        description="Enable analytics collection"
    )
    
    enable_user_tracking: bool = Field(
        default=False,
        description="Enable user tracking"
    )
    
    # ===================================
    # Testing Configuration
    # ===================================
    test_disable_external_apis: bool = Field(
        default=True,
        description="Disable external API calls in tests"
    )
    
    test_mock_ai_responses: bool = Field(
        default=True,
        description="Mock AI responses in tests"
    )
    
    # ===================================
    # MLOps Configuration
    # ===================================
    airflow_home: str = Field(
        default="/opt/airflow",
        description="Airflow home directory"
    )
    
    dags_dir: str = Field(
        default="dags",
        description="DAGs directory"
    )
    
    airflow_executor: str = Field(
        default="LocalExecutor",
        description="Airflow executor type"
    )
    
    mlflow_tracking_uri: Optional[str] = Field(
        default=None,
        description="MLflow tracking server URI"
    )
    
    # ===================================
    # Validators
    # ===================================
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment value."""
        valid_envs = ['development', 'staging', 'production', 'test']
        if v.lower() not in valid_envs:
            raise ValueError(f'Environment must be one of: {valid_envs}')
        return v.lower()
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    @validator('ocr_engine')
    def validate_ocr_engine(cls, v):
        """Validate OCR engine."""
        valid_engines = ['tesseract', 'easyocr', 'auto']
        if v.lower() not in valid_engines:
            raise ValueError(f'OCR engine must be one of: {valid_engines}')
        return v.lower()
    
    @validator('supported_formats')
    def validate_supported_formats(cls, v):
        """Validate supported formats."""
        if not v:
            raise ValueError('At least one supported format must be specified')
        
        valid_formats = ['pdf', 'docx', 'jpg', 'jpeg', 'png', 'tiff', 'bmp']
        for fmt in v:
            if fmt.lower() not in valid_formats:
                raise ValueError(f'Unsupported format: {fmt}')
        
        return [fmt.lower() for fmt in v]
    
    @validator('cors_origins')
    def validate_cors_origins(cls, v):
        """Validate CORS origins."""
        if not v:
            raise ValueError('At least one CORS origin must be specified')
        return v
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == 'development'
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == 'production'
    
    def is_test(self) -> bool:
        """Check if running in test mode."""
        return self.environment == 'test'
    
    def get_database_url(self) -> str:
        """Get appropriate database URL based on environment."""
        if self.is_test():
            return self.test_database_url
        return self.database_url or self.test_database_url
    
    def validate_required_config(self) -> None:
        """Validate that all required configuration is present."""
        missing_keys = []
        
        if not self.anthropic_api_key:
            missing_keys.append('ANTHROPIC_API_KEY')
        
        if missing_keys:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_keys)}"
            )


# Global settings instance
settings = Settings()

# Validate required configuration at startup
try:
    settings.validate_required_config()
except ValueError as e:
    print(f"Configuration Error: {e}")
    print("Please check your .env file and ensure all required variables are set.")
    exit(1)
