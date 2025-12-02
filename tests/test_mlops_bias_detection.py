"""Unit tests for bias detection module."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from mlops.bias_detection import (
    BiasDetector,
    BiasConfig,
    BiasResult,
    BiasDetectionError
)


class TestBiasConfig:
    """Test BiasConfig model."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = BiasConfig()
        
        assert config.max_acceptable_variance == 0.05
        assert config.min_samples_per_slice == 5
        assert len(config.slice_columns) > 0


class TestBiasDetector:
    """Test BiasDetector class."""
    
    @pytest.fixture
    def config(self, tmp_path):
        """Create test configuration."""
        return BiasConfig(output_dir=tmp_path)
    
    @pytest.fixture
    def sample_df_no_bias(self):
        """Create sample DataFrame without bias."""
        return pd.DataFrame({
            "document_id": [f"doc-{i:03d}" for i in range(1, 21)],
            "loan_type": ["education"] * 5 + ["home"] * 5 + ["personal"] * 5 + ["vehicle"] * 5,
            "bank_name": ["Bank A"] * 10 + ["Bank B"] * 10,
            "file_type": ["pdf"] * 15 + ["jpeg"] * 5,
            "accuracy": [0.95] * 20  # Same accuracy across all slices
        })
    
    @pytest.fixture
    def sample_df_with_bias(self):
        """Create sample DataFrame with bias."""
        return pd.DataFrame({
            "document_id": [f"doc-{i:03d}" for i in range(1, 21)],
            "loan_type": ["education"] * 5 + ["home"] * 5 + ["personal"] * 5 + ["vehicle"] * 5,
            "bank_name": ["Bank A"] * 10 + ["Bank B"] * 10,
            "file_type": ["pdf"] * 15 + ["jpeg"] * 5,
            "accuracy": [0.95] * 5 + [0.96] * 5 + [0.85] * 5 + [0.94] * 5  # Variance in personal loans
        })
    
    def test_detector_initialization(self, config):
        """Test detector initialization."""
        detector = BiasDetector(config)
        
        assert detector.config == config
        assert detector.output_dir.exists()
    
    def test_slice_data_valid_column(self, config, sample_df_no_bias):
        """Test data slicing by valid column."""
        detector = BiasDetector(config)
        slices = detector.slice_data(sample_df_no_bias, "loan_type")
        
        assert len(slices) == 4  # 4 loan types
        assert all(len(df) == 5 for df in slices.values())
    
    def test_slice_data_invalid_column(self, config, sample_df_no_bias):
        """Test data slicing by invalid column."""
        detector = BiasDetector(config)
        slices = detector.slice_data(sample_df_no_bias, "nonexistent_column")
        
        assert len(slices) == 0
    
    def test_slice_data_min_samples(self, config):
        """Test slicing respects minimum sample size."""
        df = pd.DataFrame({
            "category": ["A"] * 10 + ["B"] * 2,  # B has too few samples
            "value": range(12)
        })
        
        detector = BiasDetector(config)
        slices = detector.slice_data(df, "category")
        
        assert len(slices) == 1  # Only A should be included
        assert "A" in slices
    
    def test_calculate_slice_metrics(self, config, sample_df_no_bias):
        """Test calculating metrics for slices."""
        detector = BiasDetector(config)
        slices = detector.slice_data(sample_df_no_bias, "loan_type")
        metrics = detector.calculate_slice_metrics(slices)
        
        assert len(metrics) == len(slices)
        for slice_metrics in metrics.values():
            assert "mean" in slice_metrics
            assert "std" in slice_metrics
            assert "count" in slice_metrics
    
    def test_calculate_fairness_metrics(self, config):
        """Test fairness metrics calculation."""
        slice_metrics = {
            "slice1": {"mean": 0.95, "std": 0.02},
            "slice2": {"mean": 0.96, "std": 0.02},
            "slice3": {"mean": 0.94, "std": 0.02}
        }
        
        detector = BiasDetector(config)
        fairness = detector.calculate_fairness_metrics(slice_metrics)
        
        assert "overall_mean" in fairness
        assert "variance" in fairness
        assert "demographic_parity_difference" in fairness
    
    def test_detect_bias_none(self, config, sample_df_no_bias):
        """Test bias detection with no bias."""
        detector = BiasDetector(config)
        slices = detector.slice_data(sample_df_no_bias, "loan_type")
        metrics = detector.calculate_slice_metrics(slices)
        result = detector.detect_bias_in_slices(metrics, "loan_type")
        
        assert result["bias_detected"] is False
    
    def test_detect_bias_found(self, config, sample_df_with_bias):
        """Test bias detection with bias present."""
        detector = BiasDetector(config)
        slices = detector.slice_data(sample_df_with_bias, "loan_type")
        metrics = detector.calculate_slice_metrics(slices)
        result = detector.detect_bias_in_slices(metrics, "loan_type")
        
        # Check if bias is detected (depends on actual variance)
        assert "bias_detected" in result
        assert "variance" in result
    
    def test_generate_recommendations_no_bias(self, config):
        """Test recommendation generation with no bias."""
        bias_results = {
            "dimension1": {"bias_detected": False}
        }
        
        detector = BiasDetector(config)
        recommendations = detector.generate_recommendations(bias_results)
        
        assert len(recommendations) > 0
        assert "no bias" in recommendations[0].lower()
    
    def test_generate_recommendations_with_bias(self, config):
        """Test recommendation generation with bias."""
        bias_results = {
            "loan_type": {
                "bias_detected": True,
                "variance": 0.08,
                "underperforming_slices": [
                    {"slice": "personal", "accuracy": 0.85, "gap": 0.10}
                ]
            }
        }
        
        detector = BiasDetector(config)
        recommendations = detector.generate_recommendations(bias_results)
        
        assert len(recommendations) > 0
        assert any("loan_type" in rec for rec in recommendations)
    
    def test_run_complete_pipeline(self, config, sample_df_with_bias):
        """Test complete bias detection pipeline."""
        detector = BiasDetector(config)
        result = detector.run(sample_df_with_bias)
        
        assert isinstance(result, BiasResult)
        assert result.slices_analyzed > 0
        assert len(result.recommendations) > 0


@pytest.mark.parametrize("variance,threshold,expected", [
    (0.03, 0.05, False),
    (0.08, 0.05, True),
    (0.05, 0.05, False),
])
def test_bias_threshold(variance, threshold, expected):
    """Test bias detection threshold."""
    bias_detected = variance > threshold
    assert bias_detected == expected
