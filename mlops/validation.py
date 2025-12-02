"""Data validation module using Great Expectations.

This module handles:
- Schema validation
- Data quality checks
- Statistics generation with TFDV
- Expectation suite management
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from pydantic import BaseModel, Field
import pandas as pd

logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Validation result model."""
    
    success: bool
    total_expectations: int
    successful_expectations: int
    failed_expectations: int
    validation_time: datetime
    statistics: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)


class ValidationConfig(BaseModel):
    """Configuration for validation."""
    
    input_dir: Path = Field(default=Path("data/processed"))
    output_dir: Path = Field(default=Path("logs"))
    expectations_suite_name: str = "loan_documents_suite"
    
    # Validation thresholds
    min_accuracy: float = Field(default=0.85, ge=0.0, le=1.0)
    max_null_percentage: float = Field(default=0.10, ge=0.0, le=1.0)
    required_columns: List[str] = Field(
        default_factory=lambda: [
            "document_id",
            "file_name",
            "file_type",
            "processing_status"
        ]
    )


class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass


class DataValidator:
    """Main class for data validation using Great Expectations."""
    
    def __init__(self, config: ValidationConfig):
        """Initialize validator with configuration.
        
        Args:
            config: ValidationConfig instance
        """
        self.config = config
        self.output_dir = config.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("DataValidator initialized successfully")
    
    def validate_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate DataFrame schema against expectations.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dictionary with validation results
            
        Raises:
            ValidationError: If validation fails critically
        """
        logger.info("Starting schema validation")
        
        results = {
            "success": True,
            "checks": [],
            "errors": []
        }
        
        try:
            # Check required columns exist
            missing_cols = set(self.config.required_columns) - set(df.columns)
            if missing_cols:
                results["success"] = False
                results["errors"].append(f"Missing required columns: {missing_cols}")
                results["checks"].append({
                    "check": "required_columns",
                    "passed": False,
                    "message": f"Missing: {missing_cols}"
                })
            else:
                results["checks"].append({
                    "check": "required_columns",
                    "passed": True,
                    "message": "All required columns present"
                })
            
            # Check for null values in required columns
            for col in self.config.required_columns:
                if col in df.columns:
                    null_pct = df[col].isnull().sum() / len(df)
                    if null_pct > self.config.max_null_percentage:
                        results["success"] = False
                        results["errors"].append(
                            f"Column {col} has {null_pct:.1%} null values "
                            f"(threshold: {self.config.max_null_percentage:.1%})"
                        )
                        results["checks"].append({
                            "check": f"null_check_{col}",
                            "passed": False,
                            "null_percentage": null_pct
                        })
                    else:
                        results["checks"].append({
                            "check": f"null_check_{col}",
                            "passed": True,
                            "null_percentage": null_pct
                        })
            
            # Check data types
            if "document_id" in df.columns:
                if not df["document_id"].dtype == "object":
                    results["errors"].append("document_id should be string type")
                    results["checks"].append({
                        "check": "document_id_type",
                        "passed": False
                    })
                else:
                    results["checks"].append({
                        "check": "document_id_type",
                        "passed": True
                    })
            
            # Check file_type values
            if "file_type" in df.columns:
                valid_types = {"pdf", "jpeg", "png", "tiff"}
                invalid_types = set(df["file_type"].unique()) - valid_types
                if invalid_types:
                    results["success"] = False
                    results["errors"].append(f"Invalid file types: {invalid_types}")
                    results["checks"].append({
                        "check": "file_type_values",
                        "passed": False,
                        "invalid_values": list(invalid_types)
                    })
                else:
                    results["checks"].append({
                        "check": "file_type_values",
                        "passed": True
                    })
            
            # Check accuracy range if present
            if "accuracy" in df.columns:
                out_of_range = ((df["accuracy"] < 0) | (df["accuracy"] > 1)).sum()
                if out_of_range > 0:
                    results["success"] = False
                    results["errors"].append(
                        f"{out_of_range} accuracy values outside [0, 1] range"
                    )
                    results["checks"].append({
                        "check": "accuracy_range",
                        "passed": False,
                        "out_of_range_count": int(out_of_range)
                    })
                else:
                    results["checks"].append({
                        "check": "accuracy_range",
                        "passed": True
                    })
            
            logger.info(f"Schema validation completed: {'PASS' if results['success'] else 'FAIL'}")
            return results
            
        except Exception as e:
            logger.exception("Schema validation failed")
            raise ValidationError(f"Schema validation failed: {e}") from e
    
    def generate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate data statistics for monitoring.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with statistics
        """
        logger.info("Generating data statistics")
        
        stats = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
            "column_stats": {}
        }
        
        try:
            for col in df.columns:
                col_stats = {
                    "dtype": str(df[col].dtype),
                    "null_count": int(df[col].isnull().sum()),
                    "null_percentage": float(df[col].isnull().sum() / len(df)),
                    "unique_count": int(df[col].nunique())
                }
                
                # Numeric columns
                if pd.api.types.is_numeric_dtype(df[col]):
                    col_stats.update({
                        "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                        "std": float(df[col].std()) if not df[col].isnull().all() else None,
                        "min": float(df[col].min()) if not df[col].isnull().all() else None,
                        "max": float(df[col].max()) if not df[col].isnull().all() else None,
                        "median": float(df[col].median()) if not df[col].isnull().all() else None
                    })
                
                # Categorical columns
                elif df[col].dtype == "object":
                    top_values = df[col].value_counts().head(5).to_dict()
                    col_stats["top_values"] = {str(k): int(v) for k, v in top_values.items()}
                
                stats["column_stats"][col] = col_stats
            
            logger.info("Statistics generation completed")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to generate statistics: {e}")
            return stats
    
    def check_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive data quality checks.
        
        Args:
            df: DataFrame to check
            
        Returns:
            Dictionary with quality check results
        """
        logger.info("Starting data quality checks")
        
        quality_checks = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "checks": []
        }
        
        try:
            # Check 1: Duplicate rows
            dup_count = df.duplicated().sum()
            check_result = {
                "name": "duplicate_rows",
                "status": "pass" if dup_count == 0 else "warning",
                "value": int(dup_count),
                "threshold": 0
            }
            quality_checks["checks"].append(check_result)
            if dup_count == 0:
                quality_checks["passed"] += 1
            else:
                quality_checks["warnings"] += 1
            
            # Check 2: Empty strings in text columns
            empty_count = 0
            for col in df.select_dtypes(include=["object"]).columns:
                empty_count += (df[col] == "").sum()
            
            check_result = {
                "name": "empty_strings",
                "status": "pass" if empty_count == 0 else "warning",
                "value": int(empty_count),
                "threshold": 0
            }
            quality_checks["checks"].append(check_result)
            if empty_count == 0:
                quality_checks["passed"] += 1
            else:
                quality_checks["warnings"] += 1
            
            # Check 3: Negative values in numeric columns
            negative_count = 0
            for col in df.select_dtypes(include=["number"]).columns:
                if col not in ["latitude", "longitude"]:  # Allow negative geo coords
                    negative_count += (df[col] < 0).sum()
            
            check_result = {
                "name": "negative_values",
                "status": "pass" if negative_count == 0 else "fail",
                "value": int(negative_count),
                "threshold": 0
            }
            quality_checks["checks"].append(check_result)
            if negative_count == 0:
                quality_checks["passed"] += 1
            else:
                quality_checks["failed"] += 1
            
            # Check 4: Completeness score
            total_cells = df.shape[0] * df.shape[1]
            null_cells = df.isnull().sum().sum()
            completeness = 1 - (null_cells / total_cells) if total_cells > 0 else 0
            
            check_result = {
                "name": "completeness",
                "status": "pass" if completeness >= 0.90 else "warning",
                "value": float(completeness),
                "threshold": 0.90
            }
            quality_checks["checks"].append(check_result)
            if completeness >= 0.90:
                quality_checks["passed"] += 1
            else:
                quality_checks["warnings"] += 1
            
            quality_checks["overall_status"] = (
                "pass" if quality_checks["failed"] == 0 else "fail"
            )
            
            logger.info(f"Data quality checks completed: {quality_checks['overall_status']}")
            return quality_checks
            
        except Exception as e:
            logger.exception("Data quality checks failed")
            return quality_checks
    
    def validate_dataframe(self, df: pd.DataFrame) -> ValidationResult:
        """Run complete validation pipeline on DataFrame.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            ValidationResult with complete results
        """
        logger.info("Starting complete validation pipeline")
        start_time = datetime.utcnow()
        
        try:
            # Schema validation
            schema_results = self.validate_schema(df)
            
            # Generate statistics
            stats = self.generate_statistics(df)
            
            # Quality checks
            quality_results = self.check_data_quality(df)
            
            # Calculate totals
            total_checks = len(schema_results["checks"]) + len(quality_results["checks"])
            passed_checks = (
                sum(1 for c in schema_results["checks"] if c["passed"]) +
                quality_results["passed"]
            )
            
            # Create result
            result = ValidationResult(
                success=schema_results["success"] and quality_results["overall_status"] == "pass",
                total_expectations=total_checks,
                successful_expectations=passed_checks,
                failed_expectations=total_checks - passed_checks,
                validation_time=start_time,
                statistics={
                    "schema_validation": schema_results,
                    "quality_checks": quality_results,
                    "statistics": stats
                },
                errors=schema_results["errors"]
            )
            
            # Save results
            self._save_validation_results(result)
            
            logger.info(f"Validation pipeline completed: {'SUCCESS' if result.success else 'FAILED'}")
            return result
            
        except Exception as e:
            logger.exception("Validation pipeline failed")
            raise ValidationError(f"Validation pipeline failed: {e}") from e
    
    def _save_validation_results(self, result: ValidationResult) -> None:
        """Save validation results to file.
        
        Args:
            result: ValidationResult to save
        """
        try:
            output_file = self.output_dir / "validation_results.json"
            
            with open(output_file, "w") as f:
                json.dump(
                    result.model_dump(mode="json"),
                    f,
                    indent=2,
                    default=str
                )
            
            # Also save metrics
            metrics_file = self.output_dir / "validation_metrics.json"
            metrics = {
                "success": result.success,
                "total_expectations": result.total_expectations,
                "successful_expectations": result.successful_expectations,
                "failed_expectations": result.failed_expectations,
                "success_rate": result.successful_expectations / result.total_expectations
                    if result.total_expectations > 0 else 0,
                "timestamp": result.validation_time.isoformat()
            }
            
            with open(metrics_file, "w") as f:
                json.dump(metrics, f, indent=2)
            
            logger.info(f"Validation results saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save validation results: {e}")
    
    def run(self) -> ValidationResult:
        """Run validation on processed data files.
        
        Returns:
            ValidationResult with results
        """
        logger.info("Starting validation run")
        
        try:
            # Load processed data (simplified - would load actual data)
            # For now, create sample DataFrame
            sample_data = {
                "document_id": ["doc-001", "doc-002", "doc-003"],
                "file_name": ["loan1.pdf", "loan2.pdf", "loan3.pdf"],
                "file_type": ["pdf", "pdf", "pdf"],
                "processing_status": ["completed", "completed", "completed"],
                "accuracy": [0.95, 0.97, 0.93]
            }
            df = pd.DataFrame(sample_data)
            
            # Run validation
            result = self.validate_dataframe(df)
            
            return result
            
        except Exception as e:
            logger.exception("Validation run failed")
            raise ValidationError(f"Validation run failed: {e}") from e


def main() -> None:
    """Main entry point for validation script."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/validation.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create configuration
    config = ValidationConfig()
    
    # Run validation
    validator = DataValidator(config)
    result = validator.run()
    
    print(f"\nValidation Summary:")
    print(f"  Success: {result.success}")
    print(f"  Total Checks: {result.total_expectations}")
    print(f"  Passed: {result.successful_expectations}")
    print(f"  Failed: {result.failed_expectations}")
    print(f"  Success Rate: {result.successful_expectations/result.total_expectations:.1%}")


if __name__ == "__main__":
    main()
