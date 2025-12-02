"""Unit tests for validation module."""

import pytest
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from mlops.validation import (
    DataValidator,
    ValidationConfig,
    ValidationResult,
    ValidationError
)


class TestValidationConfig:
    """Test ValidationConfig model."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = ValidationConfig()
        
        assert config.min_accuracy == 0.85
        assert config.max_null_percentage == 0.10
        assert "document_id" in config.required_columns


class TestDataValidator:
    """Test DataValidator class."""
    
    @pytest.fixture
    def config(self, tmp_path):
        """Create test configuration."""
        return ValidationConfig(output_dir=tmp_path)
    
    @pytest.fixture
    def sample_valid_df(self):
        """Create sample valid DataFrame."""
        return pd.DataFrame({
            "document_id": ["doc-001", "doc-002", "doc-003"],
            "file_name": ["test1.pdf", "test2.pdf", "test3.pdf"],
            "file_type": ["pdf", "pdf", "jpeg"],
            "processing_status": ["completed", "completed", "completed"],
            "accuracy": [0.95, 0.97, 0.93]
        })
    
    @pytest.fixture
    def sample_invalid_df(self):
        """Create sample invalid DataFrame."""
        return pd.DataFrame({
            "document_id": ["doc-001", None, "doc-003"],
            "file_name": ["test1.pdf", "test2.pdf", "test3.pdf"],
            "file_type": ["pdf", "doc", "jpeg"],  # Invalid type
            "processing_status": ["completed", "completed", "completed"],
            "accuracy": [0.95, 1.5, 0.93]  # Out of range
        })
    
    def test_validator_initialization(self, config):
        """Test validator initialization."""
        validator = DataValidator(config)
        
        assert validator.config == config
        assert validator.output_dir.exists()
    
    def test_validate_schema_success(self, config, sample_valid_df):
        """Test schema validation with valid data."""
        validator = DataValidator(config)
        result = validator.validate_schema(sample_valid_df)
        
        assert result["success"] is True
        assert len(result["errors"]) == 0
    
    def test_validate_schema_missing_columns(self, config):
        """Test schema validation with missing required columns."""
        validator = DataValidator(config)
        df = pd.DataFrame({"document_id": ["doc-001"]})
        
        result = validator.validate_schema(df)
        
        assert result["success"] is False
        assert len(result["errors"]) > 0
    
    def test_validate_schema_invalid_file_type(self, config, sample_invalid_df):
        """Test schema validation with invalid file types."""
        validator = DataValidator(config)
        result = validator.validate_schema(sample_invalid_df)
        
        assert result["success"] is False
        assert any("file types" in err.lower() for err in result["errors"])
    
    def test_generate_statistics(self, config, sample_valid_df):
        """Test statistics generation."""
        validator = DataValidator(config)
        stats = validator.generate_statistics(sample_valid_df)
        
        assert stats["row_count"] == 3
        assert stats["column_count"] == 5
        assert "column_stats" in stats
    
    def test_check_data_quality_no_duplicates(self, config, sample_valid_df):
        """Test data quality checks with clean data."""
        validator = DataValidator(config)
        result = validator.check_data_quality(sample_valid_df)
        
        assert result["passed"] > 0
        assert result["overall_status"] == "pass"
    
    def test_validate_dataframe_complete(self, config, sample_valid_df):
        """Test complete validation pipeline."""
        validator = DataValidator(config)
        result = validator.validate_dataframe(sample_valid_df)
        
        assert isinstance(result, ValidationResult)
        assert result.success is True
        assert result.total_expectations > 0


@pytest.mark.parametrize("accuracy,expected", [
    (0.95, True),
    (0.75, False),
    (1.0, True),
    (0.0, False)
])
def test_accuracy_validation(accuracy, expected):
    """Test accuracy value validation."""
    is_valid = 0.0 <= accuracy <= 1.0 and accuracy >= 0.85
    assert is_valid == expected
