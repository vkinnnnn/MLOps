"""Unit tests for anomaly detection module."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from mlops.anomaly_detection import (
    AnomalyDetector,
    AnomalyConfig,
    AnomalyResult,
    AnomalyDetectionError
)


class TestAnomalyConfig:
    """Test AnomalyConfig model."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = AnomalyConfig()
        
        assert config.min_accuracy == 0.85
        assert config.max_processing_time == 30
        assert config.outlier_contamination == 0.05


class TestAnomalyDetector:
    """Test AnomalyDetector class."""
    
    @pytest.fixture
    def config(self, tmp_path):
        """Create test configuration."""
        return AnomalyConfig(output_dir=tmp_path)
    
    @pytest.fixture
    def sample_df_no_anomalies(self):
        """Create sample DataFrame without anomalies."""
        return pd.DataFrame({
            "document_id": [f"doc-{i:03d}" for i in range(1, 11)],
            "accuracy": [0.95, 0.96, 0.94, 0.97, 0.95, 0.96, 0.95, 0.94, 0.96, 0.95],
            "processing_time": [10, 11, 12, 10, 11, 12, 10, 11, 12, 10],
            "page_count": [5, 6, 7, 5, 6, 7, 5, 6, 7, 5]
        })
    
    @pytest.fixture
    def sample_df_with_anomalies(self):
        """Create sample DataFrame with anomalies."""
        return pd.DataFrame({
            "document_id": [f"doc-{i:03d}" for i in range(1, 11)],
            "accuracy": [0.95, 0.75, 0.94, 0.97, 0.95, 0.96, 0.95, 0.94, 0.96, 0.95],  # One low
            "processing_time": [10, 11, 50, 10, 11, 12, 10, 11, 12, 10],  # One high
            "page_count": [5, 6, 7, 200, 6, 7, 5, 6, 7, 5]  # One outlier
        })
    
    def test_detector_initialization(self, config):
        """Test detector initialization."""
        detector = AnomalyDetector(config)
        
        assert detector.config == config
        assert detector.output_dir.exists()
        assert detector.isolation_forest is not None
    
    def test_detect_outliers_with_data(self, config, sample_df_with_anomalies):
        """Test outlier detection with anomalous data."""
        detector = AnomalyDetector(config)
        predictions, outlier_indices = detector.detect_outliers(sample_df_with_anomalies)
        
        assert len(predictions) > 0
        assert isinstance(outlier_indices, list)
    
    def test_detect_accuracy_anomalies_found(self, config, sample_df_with_anomalies):
        """Test accuracy anomaly detection with low accuracy."""
        detector = AnomalyDetector(config)
        result = detector.detect_accuracy_anomalies(sample_df_with_anomalies)
        
        assert result["detected"] is True
        assert result["count"] > 0
        assert "statistics" in result
    
    def test_detect_accuracy_anomalies_none(self, config, sample_df_no_anomalies):
        """Test accuracy anomaly detection with no anomalies."""
        detector = AnomalyDetector(config)
        result = detector.detect_accuracy_anomalies(sample_df_no_anomalies)
        
        assert result["detected"] is False
        assert result["count"] == 0
    
    def test_detect_missing_values_none(self, config, sample_df_no_anomalies):
        """Test missing value detection with clean data."""
        detector = AnomalyDetector(config)
        result = detector.detect_missing_values_anomalies(sample_df_no_anomalies)
        
        assert result["detected"] is False
    
    def test_detect_missing_values_found(self, config):
        """Test missing value detection with missing data."""
        df = pd.DataFrame({
            "col1": [1, 2, None, 4],
            "col2": [None, 2, 3, 4]
        })
        
        detector = AnomalyDetector(config)
        result = detector.detect_missing_values_anomalies(df)
        
        assert result["detected"] is True
        assert len(result["columns_with_missing"]) == 2
    
    def test_run_complete_pipeline(self, config, sample_df_with_anomalies):
        """Test complete anomaly detection pipeline."""
        detector = AnomalyDetector(config)
        result = detector.run(sample_df_with_anomalies)
        
        assert isinstance(result, AnomalyResult)
        assert result.anomalies_detected >= 0
        assert result.anomaly_rate >= 0.0


@pytest.mark.parametrize("value,threshold,expected", [
    (0.95, 0.85, False),
    (0.75, 0.85, True),
    (0.85, 0.85, False),
])
def test_is_anomaly(value, threshold, expected):
    """Test anomaly detection logic."""
    is_anomaly = value < threshold
    assert is_anomaly == expected
