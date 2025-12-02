"""
Enhanced Loan Comparison Engine
AI-powered comparison with pros/cons generation and flexibility scoring
Follows KIRO Global Steering Guidelines
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class LoanMetrics:
    """Financial metrics for a single loan"""
    loan_id: str
    bank_name: str
    principal: float
    interest_rate: float
    tenure_months: int
    monthly_payment: float
    total_cost: float
    total_interest: float
    effective_rate: float
    upfront_costs: float
    processing_fee: float
    other_fees: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'loan_id': self.loan_id,
            'bank_name': self.bank_name,
            'principal': round(self.principal, 2),
            'interest_rate': round(self.interest_rate, 2),
            'tenure_months': self.tenure_months,
            'monthly_payment': round(self.monthly_payment, 2),
            'total_cost': round(self.total_cost, 2),
            'total_interest': round(self.total_interest, 2),
            'effective_rate': round(self.effective_rate, 2),
            'upfront_costs': round(self.upfront_costs, 2),
            'processing_fee': round(self.processing_fee, 2),
            'other_fees': round(self.other_fees, 2)
        }


@dataclass
class FlexibilityScore:
    """Flexibility scoring for a loan"""
    loan_id: str
    bank_name: str
    score: int  # 0-10
    features: List[str] = field(default_factory=list)
    details: Dict[str, bool] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'loan_id': self.loan_id,
            'bank_name': self.bank_name,
            'score': self.score,
            'features': self.features,
            'details': self.details
        }


@dataclass
class ProsCons:
    """Pros and cons analysis for a loan"""
    loan_id: str
    bank_name: str
    pros: List[str]
    cons: List[str]
    summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'loan_id': self.loan_id,
            'bank_name': self.bank_name,
            'pros': self.pros,
            'cons': self.cons,
            'summary': self.summary
        }


@dataclass
class ComparisonResult:
    """Complete comparison result"""
    loans: List[Dict[str, Any]]
    metrics: List[LoanMetrics]
    flexibility_scores: List[FlexibilityScore]
    pros_cons: List[ProsCons]
    best_overall: str
    best_by_category: Dict[str, str]
    recommendation: str
    comparison_date: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            'loans': self.loans,
            'metrics': [m.to_dict() for m in self.metrics],
            'flexibility_scores': [f.to_dict() for f in self.flexibility_scores],
            'pros_cons': [p.to_dict() for p in self.pros_cons],
            'best_overall': self.best_overall,
            'best_by_category': self.best_by_category,
            'recommendation': self.recommendation,
            'comparison_date': self.comparison_date.isoformat()
        }


class LoanComparisonEngine:
    """
    AI-powered loan comparison engine
    Generates insights, pros/cons, and recommendations
    """
    
    def __init__(self, use_ai: bool = False):
        """
        Initialize comparison engine
        
        Args:
            use_ai: Whether to use AI/LLM for insights (requires API key)
        """
        self.use_ai = use_ai
        
        if use_ai:
            # Note: AI initialization would go here when API keys are configured
            logger.warning("AI mode requested but not yet configured")
    
    def compare_loans(self, loans: List[Dict[str, Any]]) -> ComparisonResult:
        """
        Compare multiple loans with comprehensive analysis
        
        Args:
            loans: List of Lab3 extraction results with normalized_data
            
        Returns:
            ComparisonResult with complete analysis
            
        Raises:
            ValueError: If loans list is empty or invalid
        """
        if not loans:
            raise ValueError("At least one loan is required for comparison")
        
        if len(loans) < 2:
            logger.warning("Comparison with single loan - limited insights")
        
        try:
            # Step 1: Calculate metrics for all loans
            metrics = self._calculate_metrics(loans)
            
            # Step 2: Score flexibility
            flexibility_scores = self._score_flexibility(loans)
            
            # Step 3: Generate pros/cons
            pros_cons = self._generate_pros_cons(loans, metrics, flexibility_scores)
            
            # Step 4: Identify best options
            best_by_category = self._find_best_by_category(metrics, flexibility_scores)
            
            # Step 5: Generate recommendation
            recommendation = self._generate_recommendation(
                loans, metrics, flexibility_scores, pros_cons, best_by_category
            )
            
            # Step 6: Determine best overall
            best_overall = self._determine_best_overall(
                metrics, flexibility_scores, best_by_category
            )
            
            return ComparisonResult(
                loans=[self._extract_summary(loan) for loan in loans],
                metrics=metrics,
                flexibility_scores=flexibility_scores,
                pros_cons=pros_cons,
                best_overall=best_overall,
                best_by_category=best_by_category,
                recommendation=recommendation
            )
            
        except Exception as e:
            logger.error(f"Comparison failed: {e}", exc_info=True)
            raise
    
    def _calculate_metrics(self, loans: List[Dict[str, Any]]) -> List[LoanMetrics]:
        """Calculate financial metrics for all loans"""
        metrics = []
        
        for loan in loans:
            try:
                data = loan.get('normalized_data', {})
                
                # Extract core data
                principal = data.get('principal_amount', 0)
                rate = data.get('interest_rate', 0)
                months = data.get('tenure_months', 0)
                monthly = data.get('monthly_payment', 0)
                
                # Calculate derived metrics
                total_cost = monthly * months if monthly and months else 0
                total_interest = total_cost - principal if total_cost > principal else 0
                
                # Extract fees
                processing_fee = data.get('processing_fee', 0)
                other_fees = data.get('other_fees', 0)
                upfront_costs = processing_fee + other_fees
                
                # Calculate effective rate (includes fees)
                effective_rate = self._calculate_effective_rate(
                    principal, rate, months, processing_fee
                )
                
                metrics.append(LoanMetrics(
                    loan_id=loan.get('document_id', f"loan_{len(metrics)}"),
                    bank_name=data.get('bank_name', 'Unknown Bank'),
                    principal=principal,
                    interest_rate=rate,
                    tenure_months=months,
                    monthly_payment=monthly,
                    total_cost=total_cost,
                    total_interest=total_interest,
                    effective_rate=effective_rate,
                    upfront_costs=upfront_costs,
                    processing_fee=processing_fee,
                    other_fees=other_fees
                ))
                
            except Exception as e:
                logger.error(f"Error calculating metrics for loan: {e}")
                continue
        
        return metrics
    
    @staticmethod
    def _calculate_effective_rate(
        principal: float,
        nominal_rate: float,
        months: int,
        fees: float
    ) -> float:
        """
        Calculate effective interest rate including fees
        
        Args:
            principal: Loan amount
            nominal_rate: Stated interest rate
            months: Loan term
            fees: Upfront fees
            
        Returns:
            Effective annual rate
        """
        if principal == 0 or months == 0:
            return nominal_rate
        
        # Adjust principal for fees
        effective_principal = principal - fees
        
        if effective_principal <= 0:
            return nominal_rate
        
        # Simple approximation: adjust rate based on reduced principal
        adjustment_factor = principal / effective_principal
        effective_rate = nominal_rate * adjustment_factor
        
        return effective_rate
    
    def _score_flexibility(self, loans: List[Dict[str, Any]]) -> List[FlexibilityScore]:
        """
        Score loans on repayment flexibility (0-10)
        
        Args:
            loans: List of loan documents
            
        Returns:
            List of FlexibilityScore objects
        """
        scores = []
        
        for loan in loans:
            try:
                data = loan.get('normalized_data', {})
                bank_name = data.get('bank_name', 'Unknown Bank')
                loan_id = loan.get('document_id', f"loan_{len(scores)}")
                
                # Get full text for searching
                text = self._get_full_text(loan).lower()
                
                score = 0
                features = []
                details = {}
                
                # Check for flexibility features
                if self._has_feature(text, ['no prepayment penalty', 'prepayment allowed', 'no penalty']):
                    score += 3
                    features.append("No prepayment penalty")
                    details['prepayment_allowed'] = True
                else:
                    details['prepayment_allowed'] = False
                
                if self._has_feature(text, ['deferment', 'grace period', 'moratorium']):
                    score += 2
                    features.append("Deferment available")
                    details['deferment'] = True
                else:
                    details['deferment'] = False
                
                if self._has_feature(text, ['change payment date', 'flexible payment']):
                    score += 2
                    features.append("Flexible payment dates")
                    details['flexible_dates'] = True
                else:
                    details['flexible_dates'] = False
                
                if self._has_feature(text, ['skip', 'pause']) and 'payment' in text:
                    score += 1
                    features.append("Skip payment option")
                    details['skip_payment'] = True
                else:
                    details['skip_payment'] = False
                
                if self._has_feature(text, ['top-up', 'additional loan', 'increase loan']):
                    score += 1
                    features.append("Top-up available")
                    details['top_up'] = True
                else:
                    details['top_up'] = False
                
                if self._has_feature(text, ['partial payment', 'minimum payment']):
                    score += 1
                    features.append("Partial payment accepted")
                    details['partial_payment'] = True
                else:
                    details['partial_payment'] = False
                
                scores.append(FlexibilityScore(
                    loan_id=loan_id,
                    bank_name=bank_name,
                    score=min(score, 10),  # Cap at 10
                    features=features,
                    details=details
                ))
                
            except Exception as e:
                logger.error(f"Error scoring flexibility: {e}")
                continue
        
        return scores
    
    @staticmethod
    def _get_full_text(loan: Dict[str, Any]) -> str:
        """Extract full text from loan document"""
        try:
            return loan.get('complete_extraction', {}).get(
                'text_extraction', {}
            ).get('all_text', '')
        except Exception:
            return ''
    
    @staticmethod
    def _has_feature(text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the keywords"""
        return any(keyword in text for keyword in keywords)
    
    def _generate_pros_cons(
        self,
        loans: List[Dict[str, Any]],
        metrics: List[LoanMetrics],
        flexibility: List[FlexibilityScore]
    ) -> List[ProsCons]:
        """
        Generate pros and cons for each loan
        
        Args:
            loans: Original loan documents
            metrics: Calculated metrics
            flexibility: Flexibility scores
            
        Returns:
            List of ProsCons objects
        """
        pros_cons_list = []
        
        # Find best values for comparison
        if not metrics:
            return pros_cons_list
        
        lowest_rate = min(m.interest_rate for m in metrics if m.interest_rate > 0)
        lowest_monthly = min(m.monthly_payment for m in metrics if m.monthly_payment > 0)
        lowest_total = min(m.total_cost for m in metrics if m.total_cost > 0)
        highest_flex = max(f.score for f in flexibility)
        
        for i, metric in enumerate(metrics):
            pros = []
            cons = []
            
            # Analyze interest rate
            if metric.interest_rate == lowest_rate:
                pros.append(f"Lowest interest rate ({metric.interest_rate}%)")
            elif metric.interest_rate > lowest_rate + 1.0:
                cons.append(f"Higher interest rate than best option (+{metric.interest_rate - lowest_rate:.1f}%)")
            
            # Analyze monthly payment
            if metric.monthly_payment == lowest_monthly:
                pros.append(f"Lowest monthly payment (${metric.monthly_payment:,.2f})")
            elif metric.monthly_payment > lowest_monthly * 1.1:
                diff = metric.monthly_payment - lowest_monthly
                cons.append(f"Higher monthly payment (+${diff:,.2f}/month)")
            
            # Analyze total cost
            if metric.total_cost == lowest_total:
                pros.append(f"Lowest total cost (${metric.total_cost:,.2f})")
            else:
                savings = metric.total_cost - lowest_total
                if savings > 500:
                    cons.append(f"Higher total cost (+${savings:,.2f} over loan life)")
            
            # Analyze flexibility
            flex_score = flexibility[i] if i < len(flexibility) else FlexibilityScore('', '', 0)
            if flex_score.score == highest_flex and flex_score.score > 5:
                pros.append(f"Most flexible terms (score: {flex_score.score}/10)")
                for feature in flex_score.features[:2]:  # Top 2 features
                    pros.append(feature)
            elif flex_score.score < 3:
                cons.append("Limited repayment flexibility")
            
            # Analyze fees
            if metric.upfront_costs == 0:
                pros.append("No upfront fees")
            elif metric.upfront_costs > 500:
                cons.append(f"High upfront costs (${metric.upfront_costs:,.2f})")
            
            # Check tenure
            if metric.tenure_months <= 36:
                pros.append("Short loan term (finish debt quickly)")
            elif metric.tenure_months >= 72:
                cons.append("Long loan term (more interest over time)")
                pros.append("Lower monthly payment due to longer term")
            
            # Generate summary
            summary = self._generate_loan_summary(metric, flex_score, pros, cons)
            
            pros_cons_list.append(ProsCons(
                loan_id=metric.loan_id,
                bank_name=metric.bank_name,
                pros=pros[:5],  # Top 5 pros
                cons=cons[:5],  # Top 5 cons
                summary=summary
            ))
        
        return pros_cons_list
    
    @staticmethod
    def _generate_loan_summary(
        metric: LoanMetrics,
        flex: FlexibilityScore,
        pros: List[str],
        cons: List[str]
    ) -> str:
        """Generate a brief summary of the loan"""
        if len(pros) > len(cons):
            tone = "Strong option"
        elif len(cons) > len(pros):
            tone = "Consider carefully"
        else:
            tone = "Balanced option"
        
        return (f"{tone} with {metric.tenure_months}-month term. "
                f"Total cost: ${metric.total_cost:,.2f}. "
                f"Flexibility score: {flex.score}/10.")
    
    def _find_best_by_category(
        self,
        metrics: List[LoanMetrics],
        flexibility: List[FlexibilityScore]
    ) -> Dict[str, str]:
        """Find best loan in each category"""
        if not metrics:
            return {}
        
        best = {}
        
        # Lowest total cost
        best_cost = min(metrics, key=lambda m: m.total_cost)
        best['lowest_total_cost'] = best_cost.bank_name
        
        # Lowest monthly payment
        best_monthly = min(metrics, key=lambda m: m.monthly_payment)
        best['lowest_monthly_payment'] = best_monthly.bank_name
        
        # Lowest interest rate
        best_rate = min(metrics, key=lambda m: m.interest_rate)
        best['lowest_interest_rate'] = best_rate.bank_name
        
        # Most flexible
        if flexibility:
            best_flex = max(flexibility, key=lambda f: f.score)
            best['most_flexible'] = best_flex.bank_name
        
        # Best upfront (lowest fees)
        best_upfront = min(metrics, key=lambda m: m.upfront_costs)
        best['lowest_upfront_costs'] = best_upfront.bank_name
        
        return best
    
    def _generate_recommendation(
        self,
        loans: List[Dict[str, Any]],
        metrics: List[LoanMetrics],
        flexibility: List[FlexibilityScore],
        pros_cons: List[ProsCons],
        best_by_category: Dict[str, str]
    ) -> str:
        """
        Generate personalized recommendation
        
        Args:
            loans: Original documents
            metrics: Calculated metrics
            flexibility: Flexibility scores
            pros_cons: Pros and cons analysis
            best_by_category: Best loans by category
            
        Returns:
            Recommendation text
        """
        if not metrics:
            return "Unable to generate recommendation with provided data."
        
        # Find overall best based on weighted scoring
        scores = []
        for i, metric in enumerate(metrics):
            flex = flexibility[i] if i < len(flexibility) else FlexibilityScore('', '', 0)
            
            # Weighted score (lower is better)
            # 40% total cost, 30% flexibility, 20% monthly payment, 10% fees
            cost_score = metric.total_cost / min(m.total_cost for m in metrics)
            flex_score = (10 - flex.score) / 10  # Invert (lower is better)
            monthly_score = metric.monthly_payment / min(m.monthly_payment for m in metrics)
            fee_score = metric.upfront_costs / max(m.upfront_costs for m in metrics) if max(m.upfront_costs for m in metrics) > 0 else 0
            
            weighted = (cost_score * 0.4) + (flex_score * 0.3) + (monthly_score * 0.2) + (fee_score * 0.1)
            scores.append((weighted, i, metric))
        
        scores.sort(key=lambda x: x[0])
        best_idx = scores[0][1]
        best_metric = scores[0][2]
        second_best = scores[1][2] if len(scores) > 1 else None
        
        # Build recommendation
        recommendation = f"""**Recommendation for Student Loan:**

🏆 **Best Overall Choice: {best_metric.bank_name}**

**Why this is the best option for you:**

"""
        
        # Add key reasons
        reasons = []
        
        if best_metric.total_cost == min(m.total_cost for m in metrics):
            savings = (second_best.total_cost - best_metric.total_cost) if second_best else 0
            reasons.append(f"• **Lowest total cost** - Save ${savings:,.2f} over the loan life")
        
        if best_metric.monthly_payment <= min(m.monthly_payment for m in metrics) * 1.05:
            reasons.append(f"• **Affordable payments** - ${best_metric.monthly_payment:,.2f}/month fits student budget")
        
        flex = flexibility[best_idx] if best_idx < len(flexibility) else None
        if flex and flex.score >= 6:
            reasons.append(f"• **Good flexibility** - {', '.join(flex.features[:2])}")
        
        if best_metric.upfront_costs < 500:
            reasons.append(f"• **Low upfront costs** - Only ${best_metric.upfront_costs:,.2f} to start")
        
        recommendation += "\n".join(reasons[:4])
        
        # Add considerations
        recommendation += "\n\n**Important Considerations:**\n\n"
        
        if best_metric.tenure_months > 60:
            recommendation += "• This is a longer-term loan. Consider paying extra monthly to finish faster and save on interest.\n"
        
        if flex and not flex.details.get('prepayment_allowed', False):
            recommendation += "• Check prepayment terms if you plan to pay off early.\n"
        
        recommendation += f"• Build an emergency fund to avoid missing payments.\n"
        recommendation += f"• Total amount to repay: ${best_metric.total_cost:,.2f} (${best_metric.total_interest:,.2f} in interest)\n"
        
        # Add alternative if close
        if second_best and (scores[1][0] - scores[0][0]) < 0.1:
            recommendation += f"\n**Alternative Option:** {second_best.bank_name} is also competitive. Compare both offers carefully."
        
        return recommendation
    
    @staticmethod
    def _determine_best_overall(
        metrics: List[LoanMetrics],
        flexibility: List[FlexibilityScore],
        best_by_category: Dict[str, str]
    ) -> str:
        """Determine the best overall loan"""
        if not metrics:
            return "Unknown"
        
        # Simple heuristic: lowest total cost with decent flexibility
        best_cost = min(metrics, key=lambda m: m.total_cost)
        
        # Check if it has decent flexibility
        best_idx = next((i for i, m in enumerate(metrics) if m.loan_id == best_cost.loan_id), 0)
        flex = flexibility[best_idx] if best_idx < len(flexibility) else None
        
        if flex and flex.score >= 5:
            return best_cost.bank_name
        
        # If low flexibility, consider most flexible with reasonable cost
        if flexibility:
            most_flex = max(flexibility, key=lambda f: f.score)
            flex_idx = next((i for i, f in enumerate(flexibility) if f.loan_id == most_flex.loan_id), 0)
            flex_metric = metrics[flex_idx]
            
            # If within 10% of best cost, choose flexible option
            if flex_metric.total_cost <= best_cost.total_cost * 1.1:
                return most_flex.bank_name
        
        return best_cost.bank_name
    
    @staticmethod
    def _extract_summary(loan: Dict[str, Any]) -> Dict[str, Any]:
        """Extract summary information from loan document"""
        data = loan.get('normalized_data', {})
        return {
            'document_id': loan.get('document_id', 'unknown'),
            'document_name': loan.get('document_name', 'Unknown'),
            'bank_name': data.get('bank_name', 'Unknown Bank'),
            'loan_type': data.get('loan_type', 'Unknown'),
            'processing_date': loan.get('processed_at', datetime.utcnow().isoformat())
        }


# Create singleton instance
comparison_engine = LoanComparisonEngine()
