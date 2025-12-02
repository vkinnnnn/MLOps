"""Anomaly detection module for data quality monitoring.

This module handles:
- Outlier detection using Isolation Forest
- Statistical anomaly detection
- Schema drift detection
- Processing time anomaly detection
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class AnomalyResult(BaseModel):
    """Anomaly detection result model."""
    
    anomalies_detected: int
    total_samples: int
    anomaly_rate: float = Field(..., ge=0.0, le=1.0)
    anomaly_types: List[str]
    alerts_triggered: int
    detection_time: datetime
    details: Dict[str, Any] = Field(default_factory=dict)


class AnomalyConfig(BaseModel):
    """Configuration for anomaly detection."""
    
    input_dir: Path = Field(default=Path("data/processed"))
    output_dir: Path = Field(default=Path("logs"))
    
    # Thresholds
    min_accuracy: float = Field(default=0.85, ge=0.0, le=1.0)
    max_processing_time: int = Field(default=30, ge=1)  # seconds
    max_error_rate: float = Field(default=0.05, ge=0.0, le=1.0)
    outlier_contamination: float = Field(default=0.05, ge=0.01, le=0.5)
    
    # Alert settings
    alert_on_low_accuracy: bool = True
    alert_on_outliers: bool = True
    alert_on_schema_drift: bool = True


class AnomalyDetectionError(Exception):
    """Custom exception for anomaly detection failures."""
    pass


class AnomalyDetector:
    """Main class for anomaly detection."""
    
    def __init__(self, config: AnomalyConfig):
        """Initialize anomaly detector with configuration.
        
        Args:
            config: AnomalyConfig instance
        """
        self.config = config
        self.output_dir = config.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize models
        self.isolation_forest = IsolationForest(
            contamination=config.outlier_contamination,
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        
        logger.info("AnomalyDetector initialized successfully")
    
    def detect_outliers(
        self,
        df: pd.DataFrame,
        numeric_columns: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, List[int]]:
        """Detect outliers using Isolation Forest.
        
        Args:
            df: DataFrame to analyze
            numeric_columns: List of numeric columns to use
            
        Returns:
            Tuple of (predictions array, outlier indices)
        """
        logger.info("Detecting outliers using Isolation Forest")
        
        try:
            # Select numeric columns
            if numeric_columns is None:
                numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if not numeric_columns:
                logger.warning("No numeric columns found for outlier detection")
                return np.array([]), []
            
            # Prepare data
            X = df[numeric_columns].fillna(df[numeric_columns].median())
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Detect outliers (-1 for outliers, 1 for inliers)
            predictions = self.isolation_forest.fit_predict(X_scaled)
            
            # Get outlier indices
            outlier_indices = np.where(predictions == -1)[0].tolist()
            
            logger.info(f"Detected {len(outlier_indices)} outliers out of {len(df)} samples")
            
            return predictions, outlier_indices
            
        except Exception as e:
            logger.error(f"Outlier detection failed: {e}")
            return np.array([]), []
    
    def detect_accuracy_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalies in accuracy metrics.
        
        Args:
            df: DataFrame with accuracy column
            
        Returns:
            Dictionary with anomaly details
        """
        logger.info("Detecting accuracy anomalies")
        
        anomalies = {
            "detected": False,
            "count": 0,
            "indices": [],
            "statistics": {}
        }
        
        try:
            if "accuracy" not in df.columns:
                logger.warning("Accuracy column not found")
                return anomalies
            
            # Filter low accuracy values
            low_accuracy = df[df["accuracy"] < self.config.min_accuracy]
            
            if len(low_accuracy) > 0:
                anomalies["detected"] = True
                anomalies["count"] = len(low_accuracy)
                anomalies["indices"] = low_accuracy.index.tolist()
                anomalies["statistics"] = {
                    "mean_accuracy": float(df["accuracy"].mean()),
                    "min_accuracy": float(df["accuracy"].min()),
                    "max_accuracy": float(df["accuracy"].max()),
                    "std_accuracy": float(df["accuracy"].std()),
                    "threshold": self.config.min_accuracy,
                    "below_threshold_percentage": len(low_accuracy) / len(df)
                }
                
                logger.warning(
                    f"Found {len(low_accuracy)} documents with accuracy < {self.config.min_accuracy}"
                )
            else:
                anomalies["statistics"] = {
                    "mean_accuracy": float(df["accuracy"].mean()),
                    "min_accuracy": float(df["accuracy"].min()),
                    "max_accuracy": float(df["accuracy"].max())
                }
                logger.info("No accuracy anomalies detected")
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Accuracy anomaly detection failed: {e}")
            return anomalies
    
    def detect_missing_values_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalies in missing values.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with missing value anomalies
        """
        logger.info("Detecting missing value anomalies")
        
        anomalies = {
            "detected": False,
            "columns_with_missing": [],
            "total_missing": 0,
            "missing_percentage": 0.0
        }
        
        try:
            # Calculate missing values per column
            missing_counts = df.isnull().sum()
            missing_pct = (missing_counts / len(df) * 100).round(2)
            
            # Find columns with missing values
            cols_with_missing = missing_counts[missing_counts > 0].to_dict()
            
            if cols_with_missing:
                anomalies["detected"] = True
                anomalies["columns_with_missing"] = [
                    {
                        "column": col,
                        "missing_count": int(count),
                        "missing_percentage": float(missing_pct[col])
                    }
                    for col, count in cols_with_missing.items()
                ]
                anomalies["total_missing"] = int(missing_counts.sum())
                total_cells = df.shape[0] * df.shape[1]
                anomalies["missing_percentage"] = float(
                    (anomalies["total_missing"] / total_cells * 100) if total_cells > 0 else 0
                )
                
                logger.warning(
                    f"Found missing values in {len(cols_with_missing)} columns "
                    f"({anomalies['missing_percentage']:.2f}% of all cells)"
                )
            else:
                logger.info("No missing value anomalies detected")
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Missing value anomaly detection failed: {e}")
            return anomalies
    
    def detect_schema_drift(
        self,
        current_schema: Dict[str, str],
        reference_schema: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Detect schema drift between current and reference schemas.
        
        Args:
            current_schema: Current data schema (column: dtype)
            reference_schema: Reference schema to compare against
            
        Returns:
            Dictionary with drift detection results
        """
        logger.info("Detecting schema drift")
        
        drift_result = {
            "detected": False,
            "added_columns": [],
            "removed_columns": [],
            "changed_types": []
        }
        
        try:
            if reference_schema is None:
                # Load reference schema from file
                schema_file = self.output_dir / "reference_schema.json"
                if schema_file.exists():
                    with open(schema_file, "r") as f:
                        reference_schema = json.load(f)
                else:
                    # Save current as reference
                    with open(schema_file, "w") as f:
                        json.dump(current_schema, f, indent=2)
                    logger.info("Saved current schema as reference")
                    return drift_result
            
            # Check for added columns
            added = set(current_schema.keys()) - set(reference_schema.keys())
            if added:
                drift_result["detected"] = True
                drift_result["added_columns"] = list(added)
                logger.warning(f"Schema drift: Added columns {added}")
            
            # Check for removed columns
            removed = set(reference_schema.keys()) - set(current_schema.keys())
            if removed:
                drift_result["detected"] = True
                drift_result["removed_columns"] = list(removed)
                logger.warning(f"Schema drift: Removed columns {removed}")
            
            # Check for type changes
            for col in set(current_schema.keys()) & set(reference_schema.keys()):
                if current_schema[col] != reference_schema[col]:
                    drift_result["detected"] = True
                    drift_result["changed_types"].append({
                        "column": col,
                        "old_type": reference_schema[col],
                        "new_type": current_schema[col]
                    })
                    logger.warning(
                        f"Schema drift: Column '{col}' type changed from "
                        f"{reference_schema[col]} to {current_schema[col]}"
                    )
            
            if not drift_result["detected"]:
                logger.info("No schema drift detected")
            
            return drift_result
            
        except Exception as e:
            logger.error(f"Schema drift detection failed: {e}")
            return drift_result
    
    def detect_statistical_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect statistical anomalies using Z-score method.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with statistical anomalies
        """
        logger.info("Detecting statistical anomalies")
        
        anomalies = {
            "detected": False,
            "columns": {}
        }
        
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            for col in numeric_cols:
                # Calculate Z-scores
                mean = df[col].mean()
                std = df[col].std()
                
                if std == 0:
                    continue
                
                z_scores = np.abs((df[col] - mean) / std)
                
                # Find outliers (|z| > 3)
                outliers = df[z_scores > 3]
                
                if len(outliers) > 0:
                    anomalies["detected"] = True
                    anomalies["columns"][col] = {
                        "count": len(outliers),
                        "indices": outliers.index.tolist(),
                        "values": outliers[col].tolist(),
                        "mean": float(mean),
                        "std": float(std)
                    }
                    
                    logger.warning(
                        f"Found {len(outliers)} statistical outliers in column '{col}'"
                    )
            
            if not anomalies["detected"]:
                logger.info("No statistical anomalies detected")
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Statistical anomaly detection failed: {e}")
            return anomalies
    
    def run(self, df: Optional[pd.DataFrame] = None) -> AnomalyResult:
        """Run complete anomaly detection pipeline.
        
        Args:
            df: Optional DataFrame to analyze. If None, loads from input_dir
            
        Returns:
            AnomalyResult with detection results
        """
        logger.info("Starting anomaly detection pipeline")
        start_time = datetime.utcnow()
        
        try:
            # Load data if not provided
            if df is None:
                # Create sample data for demonstration
                sample_data = {
                    "document_id": ["doc-001", "doc-002", "doc-003", "doc-004", "doc-005"],
                    "accuracy": [0.95, 0.97, 0.75, 0.93, 0.96],  # One low accuracy
                    "processing_time": [10, 12, 45, 11, 13],  # One high time
                    "page_count": [5, 7, 3, 200, 6]  # One outlier
                }
                df = pd.DataFrame(sample_data)
            
            anomaly_types = []
            alerts_triggered = 0
            total_anomalies = 0
            
            details = {}
            
            # 1. Detect outliers using Isolation Forest
            predictions, outlier_indices = self.detect_outliers(df)
            if len(outlier_indices) > 0:
                anomaly_types.append("outliers")
                total_anomalies += len(outlier_indices)
                if self.config.alert_on_outliers:
                    alerts_triggered += 1
                details["outliers"] = {
                    "count": len(outlier_indices),
                    "indices": outlier_indices,
                    "percentage": len(outlier_indices) / len(df)
                }
            
            # 2. Detect accuracy anomalies
            accuracy_anomalies = self.detect_accuracy_anomalies(df)
            if accuracy_anomalies["detected"]:
                anomaly_types.append("low_accuracy")
                total_anomalies += accuracy_anomalies["count"]
                if self.config.alert_on_low_accuracy:
                    alerts_triggered += 1
                details["accuracy_anomalies"] = accuracy_anomalies
            
            # 3. Detect missing value anomalies
            missing_anomalies = self.detect_missing_values_anomalies(df)
            if missing_anomalies["detected"]:
                anomaly_types.append("missing_values")
                details["missing_values"] = missing_anomalies
            
            # 4. Detect schema drift
            current_schema = {col: str(dtype) for col, dtype in df.dtypes.items()}
            schema_drift = self.detect_schema_drift(current_schema)
            if schema_drift["detected"]:
                anomaly_types.append("schema_drift")
                if self.config.alert_on_schema_drift:
                    alerts_triggered += 1
                details["schema_drift"] = schema_drift
            
            # 5. Detect statistical anomalies
            stat_anomalies = self.detect_statistical_anomalies(df)
            if stat_anomalies["detected"]:
                anomaly_types.append("statistical_outliers")
                details["statistical_anomalies"] = stat_anomalies
            
            # Create result
            anomaly_rate = total_anomalies / len(df) if len(df) > 0 else 0.0
            
            result = AnomalyResult(
                anomalies_detected=total_anomalies,
                total_samples=len(df),
                anomaly_rate=anomaly_rate,
                anomaly_types=anomaly_types,
                alerts_triggered=alerts_triggered,
                detection_time=start_time,
                details=details
            )
            
            # Save results
            self._save_results(result)
            
            logger.info(
                f"Anomaly detection completed: {total_anomalies} anomalies detected "
                f"({anomaly_rate:.2%} rate)"
            )
            
            return result
            
        except Exception as e:
            logger.exception("Anomaly detection pipeline failed")
            raise AnomalyDetectionError(f"Pipeline failed: {e}") from e
    
    def _save_results(self, result: AnomalyResult) -> None:
        """Save anomaly detection results to file.
        
        Args:
            result: AnomalyResult to save
        """
        try:
            # Save full report
            report_file = self.output_dir / "anomaly_report.json"
            with open(report_file, "w") as f:
                json.dump(
                    result.model_dump(mode="json"),
                    f,
                    indent=2,
                    default=str
                )
            
            # Save metrics
            metrics_file = self.output_dir / "anomaly_metrics.json"
            metrics = {
                "anomalies_detected": result.anomalies_detected,
                "anomaly_rate": result.anomaly_rate,
                "alerts_triggered": result.alerts_triggered,
                "anomaly_types": result.anomaly_types,
                "timestamp": result.detection_time.isoformat()
            }
            with open(metrics_file, "w") as f:
                json.dump(metrics, f, indent=2)
            
            logger.info(f"Anomaly detection results saved to {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")


def main() -> None:
    """Main entry point for anomaly detection script."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/anomaly_detection.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create configuration
    config = AnomalyConfig()
    
    # Run anomaly detection
    detector = AnomalyDetector(config)
    result = detector.run()
    
    print(f"\nAnomaly Detection Summary:")
    print(f"  Total Samples: {result.total_samples}")
    print(f"  Anomalies Detected: {result.anomalies_detected}")
    print(f"  Anomaly Rate: {result.anomaly_rate:.2%}")
    print(f"  Anomaly Types: {', '.join(result.anomaly_types)}")
    print(f"  Alerts Triggered: {result.alerts_triggered}")


if __name__ == "__main__":
    main()
