"""
Output service for generating structured loan data output.

This module provides a unified interface for generating JSON output
with comparison metrics.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path

from .data_models import NormalizedLoanData, ComparisonMetrics, ComparisonResult
from .output_generator import JSONOutputGenerator
from .comparison_calculator import ComparisonMetricsCalculator


class OutputService:
    """
    Service for generating structured output documents with metrics.
    
    This service combines JSON output generation and comparison metrics
    calculation into a single interface.
    """
    
    def __init__(self, output_directory: Optional[str] = None):
        """
        Initialize the output service.
        
        Args:
            output_directory: Directory to save output files
        """
        self.output_generator = JSONOutputGenerator(output_directory)
        self.metrics_calculator = ComparisonMetricsCalculator()
    
    def generate_complete_output(
        self,
        loan_data: NormalizedLoanData,
        source_document_path: Optional[str] = None,
        save_to_file: bool = True
    ) -> Dict[str, Any]:
        """
        Generate complete output document with metrics.
        
        Args:
            loan_data: Normalized loan data
            source_document_path: Optional path to source document
            save_to_file: Whether to save to file
            
        Returns:
            Complete output document dictionary
        """
        # Calculate comparison metrics
        metrics = self.metrics_calculator.calculate_metrics(loan_data)
        
        # Generate output document
        output_doc = self.output_generator.generate_output_document(
            loan_data,
            comparison_metrics=metrics,
            save_to_file=save_to_file
        )
        
        # Link to source document if provided
        if source_document_path:
            output_doc = self.output_generator.link_to_source_document(
                output_doc,
                source_document_path
            )
        
        return output_doc
    
    def generate_comparison_output(
        self,
        loan_data_list: List[NormalizedLoanData],
        save_to_file: bool = True
    ) -> ComparisonResult:
        """
        Generate comparison output for multiple loans.
        
        Args:
            loan_data_list: List of normalized loan data
            save_to_file: Whether to save individual outputs
            
        Returns:
            ComparisonResult with all loans and metrics
        """
        # Calculate metrics for all loans
        comparison_data = self.metrics_calculator.compare_loans(loan_data_list)
        
        # Generate individual outputs if requested
        if save_to_file:
            for loan_data in loan_data_list:
                # Find corresponding metrics
                metrics = next(
                    (m for m in comparison_data["metrics"] if m.loan_id == loan_data.loan_id),
                    None
                )
                self.output_generator.generate_output_document(
                    loan_data,
                    comparison_metrics=metrics,
                    save_to_file=True
                )
        
        # Create comparison result
        comparison_result = ComparisonResult(
            loans=loan_data_list,
            metrics=comparison_data["metrics"],
            best_by_cost=comparison_data["best_by_cost"],
            best_by_flexibility=comparison_data["best_by_flexibility"],
            comparison_notes=comparison_data.get("comparison_summary", {})
        )
        
        return comparison_result
    
    def get_json_string(
        self,
        loan_data: NormalizedLoanData,
        include_metrics: bool = True,
        pretty: bool = True
    ) -> str:
        """
        Get JSON string representation of loan data.
        
        Args:
            loan_data: Normalized loan data
            include_metrics: Whether to include comparison metrics
            pretty: Whether to format with indentation
            
        Returns:
            JSON string
        """
        metrics = None
        if include_metrics:
            metrics = self.metrics_calculator.calculate_metrics(loan_data)
        
        return self.output_generator.generate_json_string(
            loan_data,
            comparison_metrics=metrics,
            pretty=pretty
        )
