"""
Financial Education Service
Provides financial literacy resources, glossary, and educational content
Follows KIRO Global Steering Guidelines
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
import math

logger = logging.getLogger(__name__)


@dataclass
class FinancialTerm:
    """Represents a financial term with explanation"""
    term: str
    category: str
    simple_explanation: str
    detailed_explanation: str
    example: str
    why_it_matters: str
    related_terms: List[str]
    translations: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'term': self.term,
            'category': self.category,
            'simple_explanation': self.simple_explanation,
            'detailed_explanation': self.detailed_explanation,
            'example': self.example,
            'why_it_matters': self.why_it_matters,
            'related_terms': self.related_terms,
            'translations': self.translations
        }


@dataclass
class ScenarioResult:
    """Result of a financial scenario simulation"""
    scenario_type: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    explanation: str
    visualization_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'scenario_type': self.scenario_type,
            'inputs': self.inputs,
            'outputs': self.outputs,
            'explanation': self.explanation,
            'visualization_data': self.visualization_data
        }


@dataclass
class BestPractice:
    """Financial best practice recommendation"""
    title: str
    category: str
    description: str
    importance: str  # 'high', 'medium', 'low'
    applicable_to: List[str]  # 'student', 'parent', 'all'
    action_items: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'title': self.title,
            'category': self.category,
            'description': self.description,
            'importance': self.importance,
            'applicable_to': self.applicable_to,
            'action_items': self.action_items
        }


class FinancialGlossary:
    """Financial terms glossary with multilingual support"""
    
    # Comprehensive glossary of financial terms
    TERMS = {
        'APR': FinancialTerm(
            term='APR (Annual Percentage Rate)',
            category='Interest & Rates',
            simple_explanation='The yearly cost of borrowing money, including interest and fees',
            detailed_explanation='APR represents the true annual cost of a loan. It includes the interest rate plus any fees or additional costs. A 10% APR means you pay $10 for every $100 borrowed per year.',
            example='If you borrow $10,000 at 10% APR, you pay approximately $1,000 in interest per year',
            why_it_matters='Lower APR = less money paid over the loan life. Always compare APRs when choosing loans.',
            related_terms=['Interest Rate', 'Effective Rate', 'Cost of Borrowing'],
            translations={
                'hi': 'वार्षिक प्रतिशत दर',
                'te': 'వార్షిక శాతం రేటు',
                'ta': 'ஆண்டு சதவீத விகிதம்',
                'es': 'Tasa de Porcentaje Anual'
            }
        ),
        
        'Principal': FinancialTerm(
            term='Principal Amount',
            category='Loan Basics',
            simple_explanation='The original amount of money you borrow',
            detailed_explanation='Principal is the base amount borrowed, before interest and fees. This is what you must repay, plus interest over time.',
            example='If you take a $10,000 loan, the principal is $10,000',
            why_it_matters='Interest is calculated on the principal. Paying extra toward principal reduces total interest.',
            related_terms=['Loan Amount', 'Borrowed Amount', 'Principal Balance'],
            translations={
                'hi': 'मूल राशि',
                'te': 'ప్రధాన మొత్తం',
                'ta': 'முதல் தொகை',
                'es': 'Monto Principal'
            }
        ),
        
        'EMI': FinancialTerm(
            term='EMI (Equated Monthly Installment)',
            category='Payments',
            simple_explanation='The fixed amount you pay every month toward your loan',
            detailed_explanation='EMI is calculated so you pay the same amount each month. It includes both principal repayment and interest. Early payments have more interest; later payments have more principal.',
            example='For a $10,000 loan at 10% for 12 months, EMI is approximately $879/month',
            why_it_matters='Knowing your EMI helps budget your monthly expenses and ensures timely payments.',
            related_terms=['Monthly Payment', 'Installment', 'Payment Schedule'],
            translations={
                'hi': 'मासिक किस्त',
                'te': 'నెలవారీ వాయిదా',
                'ta': 'மாதாந்திர தவணை',
                'es': 'Cuota Mensual'
            }
        ),
        
        'Processing Fee': FinancialTerm(
            term='Processing Fee',
            category='Fees & Charges',
            simple_explanation='Upfront charge by the lender to process your loan application',
            detailed_explanation='Processing fees typically range from 1-3% of the loan amount. This is a one-time charge paid when the loan is disbursed.',
            example='On a $10,000 loan with 2% processing fee, you pay $200 upfront',
            why_it_matters='Reduces the actual amount you receive. Factor this into your borrowing needs.',
            related_terms=['Origination Fee', 'Application Fee', 'Upfront Costs'],
            translations={
                'hi': 'प्रोसेसिंग शुल्क',
                'te': 'ప్రాసెసింగ్ రుసుము',
                'ta': 'செயல்முறை கட்டணம்',
                'es': 'Tarifa de Procesamiento'
            }
        ),
        
        'Prepayment': FinancialTerm(
            term='Prepayment',
            category='Repayment Options',
            simple_explanation='Paying off your loan early, before the scheduled end date',
            detailed_explanation='Prepayment means paying extra toward your loan principal, either partially or in full. This reduces interest costs and shortens the loan term.',
            example='Paying $100 extra per month on a $10,000 loan can save hundreds in interest',
            why_it_matters='Can significantly reduce total interest paid. Check if your loan has prepayment penalties.',
            related_terms=['Early Payment', 'Extra Payment', 'Prepayment Penalty'],
            translations={
                'hi': 'पूर्व भुगतान',
                'te': 'ముందస్తు చెల్లింపు',
                'ta': 'முன்கூட்டியே செலுத்துதல்',
                'es': 'Pago Anticipado'
            }
        ),
        
        'Default': FinancialTerm(
            term='Loan Default',
            category='Risks',
            simple_explanation='Failure to repay the loan according to the agreed terms',
            detailed_explanation='Default occurs when you miss multiple payments (typically 90+ days). This can lead to legal action, credit score damage, and collection efforts.',
            example='Missing 3 consecutive monthly payments may put your loan in default',
            why_it_matters='Severe consequences including credit damage, legal action, and difficulty getting future loans.',
            related_terms=['Delinquency', 'Non-Payment', 'Late Payment'],
            translations={
                'hi': 'डिफ़ॉल्ट (भुगतान विफलता)',
                'te': 'రుణ చెల్లింపు వైఫల్యం',
                'ta': 'கடன் தவறி',
                'es': 'Incumplimiento de Pago'
            }
        ),
        
        'Collateral': FinancialTerm(
            term='Collateral',
            category='Loan Security',
            simple_explanation='An asset you pledge as security for the loan',
            detailed_explanation='Collateral is property (house, car, etc.) that the lender can seize if you default. Secured loans have collateral; unsecured loans do not.',
            example='In a home loan, the house itself is collateral',
            why_it_matters='Secured loans typically have lower interest rates but risk losing the asset.',
            related_terms=['Security', 'Secured Loan', 'Asset'],
            translations={
                'hi': 'संपार्श्विक (गिरवी)',
                'te': 'తాకట్టు',
                'ta': 'இணை',
                'es': 'Garantía'
            }
        ),
        
        'Credit Score': FinancialTerm(
            term='Credit Score',
            category='Credit',
            simple_explanation='A number representing your creditworthiness (300-850 scale)',
            detailed_explanation='Credit scores are calculated based on payment history, debt levels, credit history length, and other factors. Higher scores mean better loan terms.',
            example='A score above 750 is excellent and gets best interest rates',
            why_it_matters='Determines loan approval and interest rates. Timely payments improve your score.',
            related_terms=['FICO Score', 'Credit Rating', 'Creditworthiness'],
            translations={
                'hi': 'क्रेडिट स्कोर',
                'te': 'క్రెడిట్ స్కోర్',
                'ta': 'கடன் மதிப்பெண்',
                'es': 'Puntaje Crediticio'
            }
        ),
        
        'Floating Rate': FinancialTerm(
            term='Floating Interest Rate',
            category='Interest & Rates',
            simple_explanation='An interest rate that changes based on market conditions',
            detailed_explanation='Floating rates are linked to benchmark rates (like LIBOR or prime rate). Your interest rate and EMI can increase or decrease over time.',
            example='If rate starts at 10% but market rates rise to 12%, your rate increases too',
            why_it_matters='Offers lower initial rates but has uncertainty. Good when rates are falling.',
            related_terms=['Variable Rate', 'Adjustable Rate', 'Market-Linked Rate'],
            translations={
                'hi': 'परिवर्तनशील ब्याज दर',
                'te': 'మారుతూ ఉండే వడ్డీ రేటు',
                'ta': 'மாறக்கூடிய வட்டி விகிதம்',
                'es': 'Tasa de Interés Variable'
            }
        ),
        
        'Fixed Rate': FinancialTerm(
            term='Fixed Interest Rate',
            category='Interest & Rates',
            simple_explanation='An interest rate that stays the same for the entire loan term',
            detailed_explanation='With a fixed rate, your interest rate and EMI remain constant, regardless of market changes. Provides payment predictability.',
            example='10% fixed rate means you always pay 10%, even if market rates change',
            why_it_matters='Predictable payments, protection from rate increases. Good when rates are rising.',
            related_terms=['Constant Rate', 'Locked Rate', 'Non-Variable Rate'],
            translations={
                'hi': 'निश्चित ब्याज दर',
                'te': 'స్థిర వడ్డీ రేటు',
                'ta': 'நிலையான வட்டி விகிதம்',
                'es': 'Tasa de Interés Fija'
            }
        ),
        
        'Grace Period': FinancialTerm(
            term='Grace Period',
            category='Repayment Options',
            simple_explanation='Time after graduation before loan repayment begins',
            detailed_explanation='For student loans, grace period (typically 6-12 months) allows you to find a job before starting payments. Interest may or may not accrue during this time.',
            example='6-month grace period after graduation before first EMI is due',
            why_it_matters='Provides breathing room to establish income before repayment begins.',
            related_terms=['Deferment', 'Moratorium', 'Payment Delay'],
            translations={
                'hi': 'छूट अवधि',
                'te': 'గ్రేస్ పీరియడ్',
                'ta': 'கருணைக் காலம்',
                'es': 'Período de Gracia'
            }
        )
    }
    
    @classmethod
    def get_term(cls, term_key: str, language: str = 'en') -> Optional[FinancialTerm]:
        """
        Get financial term explanation
        
        Args:
            term_key: Term identifier (e.g., 'APR', 'Principal')
            language: Language code for translation
            
        Returns:
            FinancialTerm object or None if not found
        """
        term = cls.TERMS.get(term_key)
        if not term:
            # Try case-insensitive search
            for key, value in cls.TERMS.items():
                if key.lower() == term_key.lower():
                    return value
        return term
    
    @classmethod
    def search_terms(cls, query: str) -> List[FinancialTerm]:
        """
        Search for terms matching query
        
        Args:
            query: Search query
            
        Returns:
            List of matching terms
        """
        query_lower = query.lower()
        results = []
        
        for term in cls.TERMS.values():
            if (query_lower in term.term.lower() or
                query_lower in term.simple_explanation.lower() or
                query_lower in term.category.lower()):
                results.append(term)
        
        return results
    
    @classmethod
    def get_all_terms(cls, category: Optional[str] = None) -> List[FinancialTerm]:
        """
        Get all terms, optionally filtered by category
        
        Args:
            category: Filter by category
            
        Returns:
            List of financial terms
        """
        if category:
            return [t for t in cls.TERMS.values() if t.category == category]
        return list(cls.TERMS.values())
    
    @classmethod
    def get_categories(cls) -> List[str]:
        """Get list of all categories"""
        return list(set(term.category for term in cls.TERMS.values()))


class ScenarioSimulator:
    """Simulates financial scenarios to help understand impact"""
    
    @staticmethod
    def simulate_extra_payment(
        principal: float,
        rate_annual: float,
        months: int,
        extra_payment: float
    ) -> ScenarioResult:
        """
        Simulate impact of extra monthly payments
        
        Args:
            principal: Loan principal
            rate_annual: Annual interest rate
            months: Original tenure
            extra_payment: Extra amount per month
            
        Returns:
            ScenarioResult with analysis
        """
        rate_monthly = rate_annual / 100 / 12
        
        # Calculate regular scenario
        if rate_monthly == 0:
            regular_payment = principal / months
        else:
            regular_payment = principal * (
                rate_monthly * (1 + rate_monthly) ** months
            ) / ((1 + rate_monthly) ** months - 1)
        
        regular_total = regular_payment * months
        regular_interest = regular_total - principal
        
        # Calculate with extra payment
        new_payment = regular_payment + extra_payment
        
        if rate_monthly == 0:
            new_months = principal / new_payment
        else:
            new_months = -math.log(
                1 - (principal * rate_monthly / new_payment)
            ) / math.log(1 + rate_monthly)
        
        new_total = new_payment * new_months
        new_interest = new_total - principal
        
        savings = regular_total - new_total
        time_saved = months - new_months
        interest_saved = regular_interest - new_interest
        
        # Create month-by-month projection for visualization
        projection = []
        balance = principal
        for month in range(min(int(months) + 1, 120)):
            if balance <= 0:
                break
            interest = balance * rate_monthly
            principal_paid = new_payment - interest
            balance -= principal_paid
            projection.append({
                'month': month + 1,
                'payment': round(new_payment, 2),
                'principal': round(principal_paid, 2),
                'interest': round(interest, 2),
                'balance': round(max(balance, 0), 2)
            })
        
        return ScenarioResult(
            scenario_type='extra_payment',
            inputs={
                'principal': principal,
                'rate_annual': rate_annual,
                'tenure_months': months,
                'extra_payment': extra_payment
            },
            outputs={
                'regular_monthly': round(regular_payment, 2),
                'regular_total': round(regular_total, 2),
                'regular_interest': round(regular_interest, 2),
                'new_monthly': round(new_payment, 2),
                'new_total': round(new_total, 2),
                'new_interest': round(new_interest, 2),
                'new_tenure_months': round(new_months, 1),
                'savings': round(savings, 2),
                'time_saved_months': round(time_saved, 1),
                'interest_saved': round(interest_saved, 2)
            },
            explanation=f"""By paying ${extra_payment:.2f} extra each month:

💰 **You save ${savings:,.2f}** over the life of the loan
⏰ **You finish {time_saved:.1f} months early**
📉 **You pay ${interest_saved:,.2f} less in interest**

Your new monthly payment would be ${new_payment:,.2f} (up from ${regular_payment:,.2f}).
New loan term: {new_months:.1f} months (down from {months} months).

This is an excellent way to reduce your debt burden if you can afford the higher payment!""",
            visualization_data={'amortization_schedule': projection[:min(len(projection), 60)]}
        )
    
    @staticmethod
    def compare_loan_tenures(
        principal: float,
        rate_annual: float,
        tenure_options: List[int]
    ) -> ScenarioResult:
        """
        Compare different loan tenure options
        
        Args:
            principal: Loan principal
            rate_annual: Annual interest rate
            tenure_options: List of tenure options in months
            
        Returns:
            ScenarioResult with comparison
        """
        rate_monthly = rate_annual / 100 / 12
        comparisons = []
        
        for months in tenure_options:
            if rate_monthly == 0:
                monthly_payment = principal / months
            else:
                monthly_payment = principal * (
                    rate_monthly * (1 + rate_monthly) ** months
                ) / ((1 + rate_monthly) ** months - 1)
            
            total_payment = monthly_payment * months
            total_interest = total_payment - principal
            
            comparisons.append({
                'tenure_months': months,
                'monthly_payment': round(monthly_payment, 2),
                'total_payment': round(total_payment, 2),
                'total_interest': round(total_interest, 2),
                'cost_per_month_saved': round(total_interest / months, 2)
            })
        
        # Find best option (lowest total cost)
        best = min(comparisons, key=lambda x: x['total_payment'])
        worst = max(comparisons, key=lambda x: x['total_payment'])
        max_savings = worst['total_payment'] - best['total_payment']
        
        explanation = f"""**Loan Tenure Comparison:**

"""
        for opt in comparisons:
            explanation += f"**{opt['tenure_months']} months:**\n"
            explanation += f"  • Monthly Payment: ${opt['monthly_payment']:,.2f}\n"
            explanation += f"  • Total Cost: ${opt['total_payment']:,.2f}\n"
            explanation += f"  • Interest Paid: ${opt['total_interest']:,.2f}\n\n"
        
        explanation += f"""💡 **Recommendation:** The {best['tenure_months']}-month option has the lowest total cost (${best['total_payment']:,.2f}).

By choosing the shortest tenure, you save ${max_savings:,.2f} compared to the longest option.

**Trade-off:** Higher monthly payment (${best['monthly_payment']:,.2f}) but much less interest over time."""
        
        return ScenarioResult(
            scenario_type='tenure_comparison',
            inputs={
                'principal': principal,
                'rate_annual': rate_annual,
                'tenure_options': tenure_options
            },
            outputs={'comparisons': comparisons, 'best_option': best},
            explanation=explanation,
            visualization_data={'comparison_chart': comparisons}
        )


class BestPracticesLibrary:
    """Library of financial best practices"""
    
    PRACTICES = [
        BestPractice(
            title='Build an Emergency Fund',
            category='Financial Safety',
            description='Save 3-6 months of expenses before or while taking a loan. This prevents missed payments during emergencies.',
            importance='high',
            applicable_to=['student', 'parent', 'all'],
            action_items=[
                'Start with a goal of $1,000 emergency fund',
                'Gradually build to 3 months of expenses',
                'Keep in a separate savings account',
                'Only use for true emergencies'
            ]
        ),
        
        BestPractice(
            title='Always Pay On Time',
            category='Payment Discipline',
            description='Timely payments build credit score, avoid late fees, and prevent default.',
            importance='high',
            applicable_to=['all'],
            action_items=[
                'Set up automatic payments if possible',
                'Mark payment dates on calendar',
                'Pay at least a few days before due date',
                'Contact lender immediately if you foresee problems'
            ]
        ),
        
        BestPractice(
            title='Read the Fine Print',
            category='Due Diligence',
            description='Understand all terms, fees, and penalties before signing.',
            importance='high',
            applicable_to=['all'],
            action_items=[
                'Review interest rate type (fixed vs floating)',
                'Check for prepayment penalties',
                'Understand late payment fees',
                'Clarify grace period terms',
                'Ask questions about unclear terms'
            ]
        ),
        
        BestPractice(
            title='Compare Multiple Offers',
            category='Loan Shopping',
            description='Never accept the first offer. Compare at least 3 lenders.',
            importance='high',
            applicable_to=['all'],
            action_items=[
                'Get quotes from 3+ lenders',
                'Compare APR, not just interest rate',
                'Consider total cost, not just monthly payment',
                'Factor in flexibility and customer service'
            ]
        ),
        
        BestPractice(
            title='Pay Extra When Possible',
            category='Debt Reduction',
            description='Even small extra payments significantly reduce total interest.',
            importance='medium',
            applicable_to=['all'],
            action_items=[
                'Round up payments (e.g., pay $200 instead of $191)',
                'Apply bonuses or tax refunds to principal',
                'Make one extra payment per year',
                'Ensure extra payments go toward principal'
            ]
        ),
        
        BestPractice(
            title='Understand Your Total Cost',
            category='Financial Awareness',
            description='Know the total amount you\'ll repay, not just the monthly payment.',
            importance='medium',
            applicable_to=['all'],
            action_items=[
                'Calculate: monthly payment × months = total cost',
                'Subtract principal to find interest paid',
                'Consider opportunity cost of that money',
                'Factor in fees and charges'
            ]
        ),
        
        BestPractice(
            title='Avoid Multiple Loans Simultaneously',
            category='Debt Management',
            description='Multiple loans increase financial stress and default risk.',
            importance='medium',
            applicable_to=['student'],
            action_items=[
                'Focus on paying off one loan before taking another',
                'If multiple loans necessary, track all carefully',
                'Prioritize high-interest loans for prepayment',
                'Consider debt consolidation if overwhelmed'
            ]
        ),
        
        BestPractice(
            title='Communicate with Your Lender',
            category='Relationship Management',
            description='Proactive communication prevents problems and shows responsibility.',
            importance='medium',
            applicable_to=['all'],
            action_items=[
                'Inform lender of address or contact changes',
                'Call immediately if you anticipate missing a payment',
                'Ask about hardship programs if needed',
                'Request payment plan modifications if circumstances change'
            ]
        ),
        
        BestPractice(
            title='Track Your Credit Score',
            category='Credit Health',
            description='Monitor your credit score to understand your financial health.',
            importance='low',
            applicable_to=['student'],
            action_items=[
                'Check credit score quarterly (free services available)',
                'Understand factors affecting your score',
                'Dispute any errors immediately',
                'Watch score improve as you make timely payments'
            ]
        ),
        
        BestPractice(
            title='Plan for Post-Graduation Finances',
            category='Career Planning',
            description='Have a realistic plan for repaying student loans after graduation.',
            importance='high',
            applicable_to=['student'],
            action_items=[
                'Research typical salaries in your field',
                'Calculate affordable monthly payment (10-15% of income)',
                'Start building emergency fund during studies',
                'Consider part-time work to reduce loan amount needed'
            ]
        )
    ]
    
    @classmethod
    def get_all_practices(
        cls,
        category: Optional[str] = None,
        applicable_to: Optional[str] = None,
        importance: Optional[str] = None
    ) -> List[BestPractice]:
        """
        Get best practices with optional filtering
        
        Args:
            category: Filter by category
            applicable_to: Filter by applicability
            importance: Filter by importance level
            
        Returns:
            List of best practices
        """
        practices = cls.PRACTICES
        
        if category:
            practices = [p for p in practices if p.category == category]
        
        if applicable_to:
            practices = [p for p in practices if applicable_to in p.applicable_to or 'all' in p.applicable_to]
        
        if importance:
            practices = [p for p in practices if p.importance == importance]
        
        return practices
    
    @classmethod
    def get_categories(cls) -> List[str]:
        """Get list of all practice categories"""
        return list(set(p.category for p in cls.PRACTICES))


class FinancialEducationService:
    """Main service for financial education"""
    
    def __init__(self):
        """Initialize financial education service"""
        self.glossary = FinancialGlossary()
        self.simulator = ScenarioSimulator()
        self.practices = BestPracticesLibrary()
    
    def explain_term(
        self,
        term: str,
        language: str = 'en',
        include_related: bool = False
    ) -> Dict[str, Any]:
        """
        Explain a financial term
        
        Args:
            term: Term to explain
            language: Language for response
            include_related: Include related terms
            
        Returns:
            Term explanation dictionary
        """
        term_obj = self.glossary.get_term(term, language)
        
        if not term_obj:
            return {
                'found': False,
                'message': f"Term '{term}' not found in glossary",
                'suggestions': [t.term for t in self.glossary.search_terms(term)[:5]]
            }
        
        result = {
            'found': True,
            'term': term_obj.to_dict()
        }
        
        if include_related:
            related = []
            for related_term in term_obj.related_terms:
                rel_obj = self.glossary.get_term(related_term)
                if rel_obj:
                    related.append({
                        'term': rel_obj.term,
                        'simple_explanation': rel_obj.simple_explanation
                    })
            result['related_terms'] = related
        
        return result
    
    def search_glossary(self, query: str) -> List[Dict[str, Any]]:
        """Search glossary"""
        results = self.glossary.search_terms(query)
        return [r.to_dict() for r in results]
    
    def get_all_terms(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all glossary terms"""
        terms = self.glossary.get_all_terms(category)
        return [t.to_dict() for t in terms]
    
    def simulate_scenario(
        self,
        scenario_type: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run financial scenario simulation
        
        Args:
            scenario_type: Type of scenario ('extra_payment', 'tenure_comparison')
            params: Scenario parameters
            
        Returns:
            Scenario result dictionary
        """
        try:
            if scenario_type == 'extra_payment':
                result = self.simulator.simulate_extra_payment(
                    principal=params['principal'],
                    rate_annual=params['rate_annual'],
                    months=params['months'],
                    extra_payment=params['extra_payment']
                )
            elif scenario_type == 'tenure_comparison':
                result = self.simulator.compare_loan_tenures(
                    principal=params['principal'],
                    rate_annual=params['rate_annual'],
                    tenure_options=params['tenure_options']
                )
            else:
                return {
                    'success': False,
                    'error': f"Unknown scenario type: {scenario_type}"
                }
            
            return {
                'success': True,
                'result': result.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Scenario simulation failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_best_practices(
        self,
        user_profile: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get best practice recommendations
        
        Args:
            user_profile: User profile with 'role' (student/parent) and optional filters
            
        Returns:
            List of best practice dictionaries
        """
        if user_profile:
            applicable_to = user_profile.get('role', 'all')
            category = user_profile.get('category')
            importance = user_profile.get('importance')
            
            practices = self.practices.get_all_practices(
                category=category,
                applicable_to=applicable_to,
                importance=importance
            )
        else:
            practices = self.practices.get_all_practices()
        
        return [p.to_dict() for p in practices]
    
    def get_learning_path(self, user_type: str = 'student') -> Dict[str, Any]:
        """
        Get recommended learning path
        
        Args:
            user_type: 'student' or 'parent'
            
        Returns:
            Structured learning path
        """
        if user_type == 'student':
            return {
                'title': 'Student Loan Mastery Path',
                'description': 'Learn everything you need to know about managing student loans',
                'modules': [
                    {
                        'order': 1,
                        'title': 'Loan Basics',
                        'topics': ['Principal', 'APR', 'EMI', 'Processing Fee'],
                        'estimated_time': '15 minutes'
                    },
                    {
                        'order': 2,
                        'title': 'Interest & Rates',
                        'topics': ['Fixed Rate', 'Floating Rate', 'Effective Rate'],
                        'estimated_time': '20 minutes'
                    },
                    {
                        'order': 3,
                        'title': 'Repayment Strategies',
                        'topics': ['Prepayment', 'Extra Payments', 'Grace Period'],
                        'estimated_time': '20 minutes'
                    },
                    {
                        'order': 4,
                        'title': 'Managing Risk',
                        'topics': ['Default', 'Credit Score', 'Emergency Fund'],
                        'estimated_time': '15 minutes'
                    },
                    {
                        'order': 5,
                        'title': 'Smart Borrowing',
                        'topics': ['Comparing Loans', 'Reading Fine Print', 'Best Practices'],
                        'estimated_time': '25 minutes'
                    }
                ],
                'total_time': '95 minutes',
                'certification': 'Smart Borrower Certificate'
            }
        else:  # parent
            return {
                'title': 'Parent\'s Guide to Student Loans',
                'description': 'Help your child make informed borrowing decisions',
                'modules': [
                    {
                        'order': 1,
                        'title': 'Understanding Loan Basics',
                        'topics': ['Principal', 'Interest Rate', 'Total Cost'],
                        'estimated_time': '15 minutes'
                    },
                    {
                        'order': 2,
                        'title': 'Evaluating Loan Offers',
                        'topics': ['APR Comparison', 'Hidden Fees', 'Terms to Watch'],
                        'estimated_time': '20 minutes'
                    },
                    {
                        'order': 3,
                        'title': 'Supporting Repayment',
                        'topics': ['Best Practices', 'Emergency Planning', 'Communication'],
                        'estimated_time': '15 minutes'
                    }
                ],
                'total_time': '50 minutes',
                'certification': 'Informed Co-Borrower Certificate'
            }


# Create singleton instance
financial_education = FinancialEducationService()
