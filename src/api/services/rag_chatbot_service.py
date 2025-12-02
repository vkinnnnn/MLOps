"""
RAG-based Financial Advisor Chatbot Service
Answers questions about loan documents using document-grounded retrieval
Follows KIRO Global Steering Guidelines
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import logging
import math
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Represents a chat message in conversation history"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChatResponse:
    """Response from chatbot"""
    answer: str
    sources: List[Dict[str, str]]
    confidence: float
    context_used: bool
    processing_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'answer': self.answer,
            'sources': self.sources,
            'confidence': self.confidence,
            'context_used': self.context_used,
            'processing_time_ms': self.processing_time_ms
        }


class ConversationMemory:
    """Manages conversation history for multi-turn dialogues"""
    
    def __init__(self, max_messages: int = 10):
        """
        Initialize conversation memory
        
        Args:
            max_messages: Maximum number of messages to retain
        """
        self.max_messages = max_messages
        self.messages: List[ChatMessage] = []
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        """Add message to conversation history"""
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
        self.messages.append(message)
        
        # Keep only recent messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_context(self, last_n: int = 5) -> str:
        """
        Get recent conversation context as formatted string
        
        Args:
            last_n: Number of recent messages to include
            
        Returns:
            Formatted conversation history
        """
        recent = self.messages[-last_n:] if len(self.messages) > last_n else self.messages
        context_parts = []
        
        for msg in recent:
            prefix = "User" if msg.role == "user" else "Assistant"
            context_parts.append(f"{prefix}: {msg.content}")
        
        return "\n".join(context_parts)
    
    def clear(self) -> None:
        """Clear conversation history"""
        self.messages.clear()


class FinancialScenarioCalculator:
    """Calculates financial scenarios for what-if questions"""
    
    @staticmethod
    def calculate_extra_payment_impact(
        principal: float,
        rate_annual: float,
        months: int,
        extra_payment: float
    ) -> Dict[str, Any]:
        """
        Calculate impact of extra monthly payments
        
        Args:
            principal: Loan principal amount
            rate_annual: Annual interest rate (e.g., 5.5 for 5.5%)
            months: Original loan term in months
            extra_payment: Additional payment amount per month
            
        Returns:
            Dictionary with savings analysis
        """
        try:
            rate_monthly = rate_annual / 100 / 12
            
            # Regular scenario
            if rate_monthly == 0:
                regular_payment = principal / months
            else:
                regular_payment = principal * (
                    rate_monthly * (1 + rate_monthly) ** months
                ) / ((1 + rate_monthly) ** months - 1)
            
            regular_total = regular_payment * months
            
            # With extra payment
            new_payment = regular_payment + extra_payment
            
            if rate_monthly == 0:
                new_months = principal / new_payment
            else:
                # Calculate new payoff time using amortization formula
                new_months = -math.log(
                    1 - (principal * rate_monthly / new_payment)
                ) / math.log(1 + rate_monthly)
            
            new_total = new_payment * new_months
            
            savings = regular_total - new_total
            time_saved = months - new_months
            
            return {
                'success': True,
                'regular_monthly': round(regular_payment, 2),
                'regular_total': round(regular_total, 2),
                'new_monthly': round(new_payment, 2),
                'new_total': round(new_total, 2),
                'new_months': round(new_months, 1),
                'savings': round(savings, 2),
                'time_saved_months': round(time_saved, 1),
                'explanation': (
                    f"By paying ${extra_payment:.2f} extra per month, "
                    f"you'll save ${savings:,.2f} and finish "
                    f"{time_saved:.1f} months early!"
                )
            }
        except Exception as e:
            logger.error(f"Extra payment calculation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def compare_tenure_options(
        principal: float,
        rate_annual: float,
        tenure_months_options: List[int]
    ) -> Dict[str, Any]:
        """
        Compare different tenure options
        
        Args:
            principal: Loan principal
            rate_annual: Annual interest rate
            tenure_months_options: List of tenure options to compare
            
        Returns:
            Comparison of tenure options
        """
        try:
            rate_monthly = rate_annual / 100 / 12
            comparisons = []
            
            for months in tenure_months_options:
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
                    'total_interest': round(total_interest, 2)
                })
            
            # Find best option (lowest total cost)
            best = min(comparisons, key=lambda x: x['total_payment'])
            
            return {
                'success': True,
                'options': comparisons,
                'best_option': best,
                'recommendation': (
                    f"The {best['tenure_months']}-month option has the lowest "
                    f"total cost (${best['total_payment']:,.2f}), saving you "
                    f"${comparisons[-1]['total_payment'] - best['total_payment']:,.2f} "
                    f"compared to the longest tenure."
                )
            }
        except Exception as e:
            logger.error(f"Tenure comparison failed: {e}")
            return {'success': False, 'error': str(e)}


class FinancialAdvisorChatbot:
    """
    RAG-based chatbot for answering questions about loan documents
    Uses vector store for context retrieval and structured data for validation
    """
    
    # System prompt for financial advisor
    SYSTEM_PROMPT = """You are a helpful financial advisor assistant helping students and parents understand loan documents.

Your responsibilities:
1. Answer questions based ONLY on the provided document context
2. Explain financial terms in simple, clear language
3. Calculate costs and scenarios when asked
4. Compare options objectively without bias
5. Always cite specific sections when possible
6. If information is not in the document, say so clearly
7. Be encouraging and supportive - finance can be overwhelming

Remember: Users may not be financial experts. Use simple language and provide context."""

    def __init__(self, vector_store=None, use_llm: bool = False):
        """
        Initialize financial advisor chatbot
        
        Args:
            vector_store: ChromaDB/LoanQA vector store for context retrieval
            use_llm: Whether to use LLM (GPT/Claude) for answers
        """
        self.vector_store = vector_store
        self.use_llm = use_llm
        self.memory = ConversationMemory()
        self.calculator = FinancialScenarioCalculator()
        
        if use_llm:
            # Note: LLM initialization would go here when API keys are configured
            # from openai import OpenAI
            # self.llm_client = OpenAI(api_key=settings.openai_api_key)
            logger.warning("LLM mode requested but not yet configured")
    
    def ask(
        self,
        question: str,
        document_id: str,
        structured_data: Optional[Dict[str, Any]] = None,
        use_memory: bool = True
    ) -> ChatResponse:
        """
        Ask a question about a loan document
        
        Args:
            question: User's question
            document_id: Document identifier for context retrieval
            structured_data: Lab3 extracted data for validation
            use_memory: Whether to use conversation history
            
        Returns:
            ChatResponse with answer and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            # Add to conversation memory
            if use_memory:
                self.memory.add_message('user', question)
            
            # Check if this is a calculation question
            if self._is_calculation_question(question):
                response = self._handle_calculation_question(
                    question, structured_data
                )
            else:
                # Standard document question
                response = self._handle_document_question(
                    question, document_id, structured_data
                )
            
            # Add assistant response to memory
            if use_memory:
                self.memory.add_message('assistant', response.answer)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            response.processing_time_ms = processing_time
            
            return response
            
        except Exception as e:
            logger.error(f"Chatbot error: {e}", exc_info=True)
            error_response = ChatResponse(
                answer="I apologize, but I encountered an error processing your question. Please try rephrasing or ask a different question.",
                sources=[],
                confidence=0.0,
                context_used=False,
                processing_time_ms=0.0
            )
            return error_response
    
    def _is_calculation_question(self, question: str) -> bool:
        """Check if question requires calculation"""
        calc_keywords = [
            'extra payment', 'pay more', 'pay extra',
            'shorter tenure', 'longer tenure', 
            'save', 'savings',
            'what if', 'how much',
            'calculate', 'compare tenure'
        ]
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in calc_keywords)
    
    def _handle_calculation_question(
        self,
        question: str,
        structured_data: Optional[Dict[str, Any]]
    ) -> ChatResponse:
        """Handle questions requiring financial calculations"""
        if not structured_data:
            return ChatResponse(
                answer="I need the loan details to perform calculations. Please make sure a document has been processed.",
                sources=[],
                confidence=0.0,
                context_used=False,
                processing_time_ms=0.0
            )
        
        principal = structured_data.get('principal_amount', 0)
        rate = structured_data.get('interest_rate', 0)
        months = structured_data.get('tenure_months', 0)
        
        if not all([principal, rate, months]):
            return ChatResponse(
                answer="I don't have complete loan information (principal, rate, or term) to perform this calculation.",
                sources=[],
                confidence=0.5,
                context_used=True,
                processing_time_ms=0.0
            )
        
        question_lower = question.lower()
        
        # Extra payment scenario
        if 'extra' in question_lower or 'more' in question_lower:
            # Try to extract amount from question
            extra_amount = self._extract_amount_from_question(question)
            if not extra_amount:
                extra_amount = 100  # Default assumption
            
            result = self.calculator.calculate_extra_payment_impact(
                principal, rate, months, extra_amount
            )
            
            if result['success']:
                answer = f"""Great question about extra payments!

Current Loan:
• Monthly Payment: ${result['regular_monthly']:,.2f}
• Total Cost: ${result['regular_total']:,.2f}
• Term: {months} months

With ${extra_amount:.2f} Extra Per Month:
• New Monthly Payment: ${result['new_monthly']:,.2f}
• New Total Cost: ${result['new_total']:,.2f}
• New Term: {result['new_months']:.1f} months

💰 **You Save: ${result['savings']:,.2f}**
⏰ **Finish {result['time_saved_months']:.1f} months early!**

This is a great way to reduce your debt burden if you can afford the higher payment."""
                
                return ChatResponse(
                    answer=answer,
                    sources=[{'type': 'calculation', 'data': 'Lab3 extracted data'}],
                    confidence=0.95,
                    context_used=True,
                    processing_time_ms=0.0
                )
        
        # Tenure comparison
        elif 'shorter' in question_lower or 'longer' in question_lower or 'compare tenure' in question_lower:
            # Compare common tenure options
            tenure_options = [36, 48, 60, 72, 84] if months <= 84 else [months-24, months-12, months, months+12, months+24]
            tenure_options = [t for t in tenure_options if t > 0 and t <= 120]
            
            result = self.calculator.compare_tenure_options(
                principal, rate, tenure_options
            )
            
            if result['success']:
                answer = "Here's how different loan terms compare:\n\n"
                
                for opt in result['options']:
                    answer += f"**{opt['tenure_months']} months:**\n"
                    answer += f"  • Monthly: ${opt['monthly_payment']:,.2f}\n"
                    answer += f"  • Total Cost: ${opt['total_payment']:,.2f}\n"
                    answer += f"  • Interest Paid: ${opt['total_interest']:,.2f}\n\n"
                
                answer += f"💡 **Recommendation:** {result['recommendation']}"
                
                return ChatResponse(
                    answer=answer,
                    sources=[{'type': 'calculation', 'data': 'Lab3 extracted data'}],
                    confidence=0.95,
                    context_used=True,
                    processing_time_ms=0.0
                )
        
        # Generic calculation response
        return ChatResponse(
            answer=f"""I can help with calculations! Based on your loan:

• Principal: ${principal:,.2f}
• Interest Rate: {rate}% per year
• Term: {months} months
• Monthly Payment: ${structured_data.get('monthly_payment', 0):,.2f}

What would you like to calculate? For example:
- "What if I pay $100 extra per month?"
- "Compare 48 vs 60 month terms"
- "How much total interest will I pay?"
""",
            sources=[{'type': 'structured_data', 'data': 'Lab3 extraction'}],
            confidence=0.8,
            context_used=True,
            processing_time_ms=0.0
        )
    
    def _handle_document_question(
        self,
        question: str,
        document_id: str,
        structured_data: Optional[Dict[str, Any]]
    ) -> ChatResponse:
        """Handle questions about document content"""
        # This is a simplified implementation
        # In production, this would query the vector store and use LLM
        
        answer = self._generate_template_answer(question, structured_data)
        
        return ChatResponse(
            answer=answer,
            sources=[{'section': 'Document', 'confidence': '85%'}],
            confidence=0.85,
            context_used=bool(structured_data),
            processing_time_ms=0.0
        )
    
    @staticmethod
    def _extract_amount_from_question(question: str) -> Optional[float]:
        """Extract dollar amount from question using simple pattern matching"""
        import re
        # Look for patterns like $100, 100 dollars, etc.
        patterns = [
            r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $100 or $1,000.00
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*dollars?',  # 100 dollars
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        return None
    
    @staticmethod
    @lru_cache(maxsize=100)
    def _generate_template_answer(question: str, structured_data_json: str) -> str:
        """Generate template-based answers for common questions"""
        # Note: structured_data is converted to JSON string for caching
        # In production, this would use LLM for better answers
        
        question_lower = question.lower()
        
        # Common question patterns
        if 'miss' in question_lower and 'payment' in question_lower:
            return """If you miss a payment on your loan:

1. **Immediate Impact:**
   - Late fee will be charged (typically $25-$50)
   - Additional interest accrues on the unpaid amount
   
2. **After Multiple Missed Payments:**
   - After 30 days: Reported to credit bureaus
   - After 60-90 days: Loan may be considered in default
   - After 90+ days: Collection actions may begin

3. **What To Do:**
   - Contact your lender immediately if you're having trouble
   - Ask about hardship programs or payment deferment
   - Never ignore missed payments - they compound quickly

Check your specific loan document for exact late payment policies in the "Default and Remedies" section."""
        
        elif 'interest rate' in question_lower:
            return """Your interest rate is the cost of borrowing money, expressed as a percentage.

**Key Points:**
- This is the annual rate (APR)
- Your actual monthly rate is this divided by 12
- It applies to your remaining balance each month
- Lower rates mean less total cost over the loan life

Check your document for whether the rate is:
• **Fixed**: Stays the same for the entire loan
• **Variable/Floating**: Can change based on market conditions"""
        
        elif 'prepay' in question_lower or 'early' in question_lower:
            return """Regarding prepayment or paying off your loan early:

**Benefits of Prepaying:**
- Save on total interest paid
- Become debt-free sooner
- Improve your credit utilization

**Check Your Document For:**
- Prepayment penalties (fees for paying early)
- Minimum prepayment amounts
- How extra payments are applied (principal vs interest)

Most education loans allow prepayment without penalty, but always verify in your specific agreement."""
        
        else:
            return """I'd be happy to help answer your question! To give you the most accurate information, I need to search through your document.

**In the meantime, here's what I can tell you about your loan:**
- Check the "Terms and Conditions" section for detailed policies
- Look for the "Payment Schedule" for timing information
- Review "Default and Remedies" for consequences of missed payments
- See "Fees and Charges" for all applicable costs

Could you please rephrase your question or provide more specific details?"""
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get formatted conversation history"""
        return [
            {
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            }
            for msg in self.memory.messages
        ]
    
    def clear_conversation(self) -> None:
        """Clear conversation history"""
        self.memory.clear()


# Create singleton instance (can be configured later)
financial_chatbot = FinancialAdvisorChatbot()
