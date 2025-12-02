"""
Multi-document comparison service for loan analysis.

This service enables comparison of multiple loan documents, identifying
the best options by cost and flexibility, and generating pros/cons analysis.
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from .data_models import (
    NormalizedLoanData,
    ComparisonMetrics,
    ComparisonResult,
    LoanType
)
from .comparison_calculator import ComparisonMetricsCalculator


logger = logging.getLogger(__name__)


class LoanComparison:
    """Detailed comparison data for a single loan."""
    
    def __init__(
        self,
        loan_data: NormalizedLoanData,
        metrics: ComparisonMetrics,
        pros: List[str],
        cons: List[str]
    ):
        self.loan_data = loan_data
        self.metrics = metrics
        self.pros = pros
        self.cons = cons
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "loan_id": self.loan_data.loan_id,
            "document_id": self.loan_data.document_id,
            "loan_type": self.loan_data.loan_type.value,
            "bank_name": self.loan_data.bank_info.bank_name if self.loan_data.bank_info else "Unknown",
            "key_fields": {
                "principal_amount": self.loan_data.principal_amount,
                "interest_rate": self.loan_data.interest_rate,
                "tenure_months": self.loan_data.tenure_months,
                "moratorium_period_months": self.loan_data.moratorium_period_months,
                "processing_fee": self.loan_data.processing_fee,
                "repayment_mode": self.loan_data.repayment_mode,
            },
            "metrics": {
                "total_cost_estimate": self.metrics.total_cost_estimate,
                "effective_interest_rate": self.metrics.effective_interest_rate,
                "flexibility_score": self.metrics.flexibility_score,
                "monthly_emi": self.metrics.monthly_emi,
                "total_interest_payable": self.metrics.total_interest_payable,
            },
            "pros": self.pros,
            "cons": self.cons
        }


class ComparisonService:
    """
    Service for comparing multiple loan documents.
    
    This service orchestrates multi-document comparison, calculating metrics,
    identifying best options, and generating pros/cons analysis.
    """
    
    def __init__(self):
        """Initialize the comparison service."""
        self.calculator = ComparisonMetricsCalculator()
    
    def compare_loans(
        self,
        loan_data_list: List[NormalizedLoanData]
    ) -> ComparisonResult:
        """
        Compare multiple loan documents.
        
        Args:
            loan_data_list: List of normalized loan data to compare
            
        Returns:
            ComparisonResult with detailed comparison analysis
            
        Raises:
            ValueError: If loan_data_list is empty or contains invalid data
        """
        if not loan_data_list:
            raise ValueError("Cannot compare empty list of loans")
        
        if len(loan_data_list) < 2:
            logger.warning("Comparing single loan - limited comparison insights")
        
        logger.info(f"Starting comparison of {len(loan_data_list)} loans")
        
        # Calculate metrics for all loans
        metrics_list = []
        for loan_data in loan_data_list:
            try:
                metrics = self.calculator.calculate_metrics(loan_data)
                metrics_list.append(metrics)
            except Exception as e:
                logger.error(f"Failed to calculate metrics for loan {loan_data.loan_id}: {e}")
                # Create default metrics for failed calculation
                metrics_list.append(self._create_default_metrics(loan_data.loan_id))
        
        # Identify best options
        best_by_cost = self._identify_best_by_cost(metrics_list)
        best_by_flexibility = self._identify_best_by_flexibility(metrics_list)
        
        # Generate comparison notes
        comparison_notes = self._generate_comparison_notes(
            loan_data_list,
            metrics_list,
            best_by_cost,
            best_by_flexibility
        )
        
        logger.info(f"Comparison complete - Best by cost: {best_by_cost}, Best by flexibility: {best_by_flexibility}")
        
        return ComparisonResult(
            loans=loan_data_list,
            metrics=metrics_list,
            best_by_cost=best_by_cost,
            best_by_flexibility=best_by_flexibility,
            comparison_notes=comparison_notes
        )
    
    def generate_comparison_table(
        self,
        loan_data_list: List[NormalizedLoanData]
    ) -> Dict[str, Any]:
        """
        Generate a comparison table with key fields for all loans.
        
        Args:
            loan_data_list: List of normalized loan data
            
        Returns:
            Dictionary containing comparison table data
        """
        if not loan_data_list:
            return {"headers": [], "rows": []}
        
        # Define table headers
        headers = [
            "Loan ID",
            "Bank",
            "Loan Type",
            "Principal Amount",
            "Interest Rate (%)",
            "Tenure (months)",
            "Processing Fee",
            "Total Cost",
            "Monthly EMI",
            "Flexibility Score"
        ]
        
        # Generate rows
        rows = []
        for loan_data in loan_data_list:
            metrics = self.calculator.calculate_metrics(loan_data)
            
            row = [
                loan_data.loan_id,
                loan_data.bank_info.bank_name if loan_data.bank_info else "Unknown",
                loan_data.loan_type.value,
                f"{loan_data.currency} {loan_data.principal_amount:,.2f}" if loan_data.principal_amount else "N/A",
                f"{loan_data.interest_rate:.2f}" if loan_data.interest_rate else "N/A",
                str(loan_data.tenure_months) if loan_data.tenure_months else "N/A",
                f"{loan_data.currency} {loan_data.processing_fee:,.2f}" if loan_data.processing_fee else "N/A",
                f"{loan_data.currency} {metrics.total_cost_estimate:,.2f}",
                f"{loan_data.currency} {metrics.monthly_emi:,.2f}" if metrics.monthly_emi else "N/A",
                f"{metrics.flexibility_score:.1f}/10.0"
            ]
            rows.append(row)
        
        return {
            "headers": headers,
            "rows": rows,
            "row_count": len(rows)
        }
    
    def generate_pros_and_cons(
        self,
        loan_data: NormalizedLoanData,
        metrics: ComparisonMetrics,
        all_metrics: List[ComparisonMetrics]
    ) -> Dict[str, List[str]]:
        """
        Generate pros and cons for a specific loan.
        
        Args:
            loan_data: Normalized loan data
            metrics: Comparison metrics for this loan
            all_metrics: Metrics for all loans being compared
            
        Returns:
            Dictionary with 'pros' and 'cons' lists
        """
        pros = []
        cons = []
        
        # Compare against other loans
        avg_cost = sum(m.total_cost_estimate for m in all_metrics) / len(all_metrics)
        avg_rate = sum(m.effective_interest_rate for m in all_metrics) / len(all_metrics)
        avg_flexibility = sum(m.flexibility_score for m in all_metrics) / len(all_metrics)
        
        min_cost = min(m.total_cost_estimate for m in all_metrics)
        max_cost = max(m.total_cost_estimate for m in all_metrics)
        min_rate = min(m.effective_interest_rate for m in all_metrics)
        max_flexibility = max(m.flexibility_score for m in all_metrics)
        
        # Cost analysis
        if metrics.total_cost_estimate == min_cost:
            pros.append("Lowest total cost among all options")
        elif metrics.total_cost_estimate <= avg_cost * 1.05:
            pros.append("Competitive total cost")
        elif metrics.total_cost_estimate >= max_cost * 0.95:
            cons.append("Highest total cost among options")
        
        # Interest rate analysis
        if metrics.effective_interest_rate == min_rate:
            pros.append("Lowest effective interest rate")
        elif metrics.effective_interest_rate <= avg_rate:
            pros.append("Below-average interest rate")
        else:
            cons.append("Above-average interest rate")
        
        # Flexibility analysis
        if metrics.flexibility_score == max_flexibility:
            pros.append("Most flexible repayment terms")
        elif metrics.flexibility_score >= avg_flexibility:
            pros.append("Good repayment flexibility")
        else:
            cons.append("Limited repayment flexibility")
        
        # Moratorium period
        if loan_data.moratorium_period_months:
            if loan_data.moratorium_period_months >= 12:
                pros.append(f"Generous moratorium period of {loan_data.moratorium_period_months} months")
            elif loan_data.moratorium_period_months >= 6:
                pros.append(f"Moratorium period of {loan_data.moratorium_period_months} months available")
        else:
            cons.append("No moratorium period")
        
        # Prepayment penalty
        if loan_data.prepayment_penalty:
            penalty_lower = loan_data.prepayment_penalty.lower()
            if 'no penalty' in penalty_lower or 'nil' in penalty_lower:
                pros.append("No prepayment penalty")
            else:
                cons.append(f"Prepayment penalty: {loan_data.prepayment_penalty}")
        
        # Processing fee
        if loan_data.processing_fee:
            if loan_data.processing_fee == 0:
                pros.append("No processing fee")
            elif loan_data.principal_amount and (loan_data.processing_fee / loan_data.principal_amount) < 0.01:
                pros.append("Low processing fee")
            elif loan_data.principal_amount and (loan_data.processing_fee / loan_data.principal_amount) > 0.03:
                cons.append("High processing fee")
        
        # Co-signer requirement
        if loan_data.co_signer:
            cons.append("Requires co-signer")
        else:
            pros.append("No co-signer required")
        
        # Collateral requirement
        if loan_data.collateral_details:
            cons.append(f"Requires collateral: {loan_data.collateral_details}")
        else:
            pros.append("No collateral required")
        
        # Ensure we have at least some pros and cons
        if not pros:
            pros.append("Standard loan terms")
        if not cons:
            cons.append("No significant drawbacks identified")
        
        return {
            "pros": pros,
            "cons": cons
        }
    
    def generate_detailed_comparison(
        self,
        loan_data_list: List[NormalizedLoanData]
    ) -> List[Dict[str, Any]]:
        """
        Generate detailed comparison with pros/cons for each loan.
        
        Args:
            loan_data_list: List of normalized loan data
            
        Returns:
            List of detailed comparison dictionaries
        """
        if not loan_data_list:
            return []
        
        # Calculate metrics for all loans
        metrics_list = [self.calculator.calculate_metrics(loan) for loan in loan_data_list]
        
        # Generate pros/cons for each loan
        detailed_comparisons = []
        for loan_data, metrics in zip(loan_data_list, metrics_list):
            pros_cons = self.generate_pros_and_cons(loan_data, metrics, metrics_list)
            
            comparison = LoanComparison(
                loan_data=loan_data,
                metrics=metrics,
                pros=pros_cons["pros"],
                cons=pros_cons["cons"]
            )
            detailed_comparisons.append(comparison.to_dict())
        
        return detailed_comparisons
    
    def _identify_best_by_cost(self, metrics_list: List[ComparisonMetrics]) -> Optional[str]:
        """Identify loan with lowest total cost."""
        if not metrics_list:
            return None
        
        best_metric = min(metrics_list, key=lambda m: m.total_cost_estimate)
        return best_metric.loan_id
    
    def _identify_best_by_flexibility(self, metrics_list: List[ComparisonMetrics]) -> Optional[str]:
        """Identify loan with highest flexibility score."""
        if not metrics_list:
            return None
        
        best_metric = max(metrics_list, key=lambda m: m.flexibility_score)
        return best_metric.loan_id
    
    def _generate_comparison_notes(
        self,
        loan_data_list: List[NormalizedLoanData],
        metrics_list: List[ComparisonMetrics],
        best_by_cost: Optional[str],
        best_by_flexibility: Optional[str]
    ) -> Dict[str, str]:
        """Generate summary notes for the comparison."""
        notes = {}
        
        if not loan_data_list or not metrics_list:
            return notes
        
        # Overall summary
        notes["summary"] = f"Compared {len(loan_data_list)} loan options"
        
        # Cost range
        costs = [m.total_cost_estimate for m in metrics_list]
        notes["cost_range"] = f"Total cost ranges from {min(costs):,.2f} to {max(costs):,.2f}"
        
        # Interest rate range
        rates = [m.effective_interest_rate for m in metrics_list]
        notes["rate_range"] = f"Effective interest rate ranges from {min(rates):.2f}% to {max(rates):.2f}%"
        
        # Flexibility range
        flex_scores = [m.flexibility_score for m in metrics_list]
        notes["flexibility_range"] = f"Flexibility scores range from {min(flex_scores):.1f} to {max(flex_scores):.1f}"
        
        # Best options
        if best_by_cost:
            notes["best_cost"] = f"Loan {best_by_cost} offers the lowest total cost"
        
        if best_by_flexibility:
            notes["best_flexibility"] = f"Loan {best_by_flexibility} offers the most flexible terms"
        
        # Recommendation
        if best_by_cost == best_by_flexibility:
            notes["recommendation"] = f"Loan {best_by_cost} is the best overall option (lowest cost and most flexible)"
        else:
            notes["recommendation"] = "Consider your priorities: choose based on cost savings or repayment flexibility"
        
        return notes
    
    def _create_default_metrics(self, loan_id: str) -> ComparisonMetrics:
        """Create default metrics for failed calculations."""
        return ComparisonMetrics(
            loan_id=loan_id,
            total_cost_estimate=0.0,
            effective_interest_rate=0.0,
            flexibility_score=0.0,
            monthly_emi=None,
            total_interest_payable=0.0,
            calculation_timestamp=datetime.now()
        )


# Convenience functions

def compare_multiple_loans(
    loan_data_list: List[NormalizedLoanData]
) -> ComparisonResult:
    """
    Convenience function to compare multiple loans.
    
    Args:
        loan_data_list: List of normalized loan data
        
    Returns:
        ComparisonResult with detailed analysis
    """
    service = ComparisonService()
    return service.compare_loans(loan_data_list)


def generate_comparison_table(
    loan_data_list: List[NormalizedLoanData]
) -> Dict[str, Any]:
    """
    Convenience function to generate comparison table.
    
    Args:
        loan_data_list: List of normalized loan data
        
    Returns:
        Dictionary with comparison table data
    """
    service = ComparisonService()
    return service.generate_comparison_table(loan_data_list)
