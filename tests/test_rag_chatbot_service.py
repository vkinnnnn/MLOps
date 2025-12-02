"""
Tests for RAG Chatbot Service
Following KIRO Global Steering Guidelines
"""

import pytest
from datetime import datetime
from src.api.services.rag_chatbot_service import (
    FinancialAdvisorChatbot,
    ConversationMemory,
    FinancialScenarioCalculator,
    ChatMessage,
    ChatResponse
)


class TestConversationMemory:
    """Test suite for ConversationMemory"""
    
    @pytest.fixture
    def memory(self):
        """Provide conversation memory instance"""
        return ConversationMemory(max_messages=5)
    
    def test_add_message(self, memory):
        """Test adding messages to memory"""
        memory.add_message('user', 'Hello')
        assert len(memory.messages) == 1
        assert memory.messages[0].role == 'user'
        assert memory.messages[0].content == 'Hello'
    
    def test_max_messages_limit(self, memory):
        """Test that memory respects max_messages limit"""
        # Add more than max
        for i in range(10):
            memory.add_message('user', f'Message {i}')
        
        assert len(memory.messages) == 5
        assert memory.messages[-1].content == 'Message 9'
    
    def test_get_context(self, memory):
        """Test getting formatted context"""
        memory.add_message('user', 'What is APR?')
        memory.add_message('assistant', 'APR is Annual Percentage Rate')
        
        context = memory.get_context()
        assert 'User: What is APR?' in context
        assert 'Assistant: APR is Annual Percentage Rate' in context
    
    def test_clear(self, memory):
        """Test clearing conversation history"""
        memory.add_message('user', 'Hello')
        memory.add_message('assistant', 'Hi there')
        
        memory.clear()
        assert len(memory.messages) == 0


class TestFinancialScenarioCalculator:
    """Test suite for FinancialScenarioCalculator"""
    
    @pytest.fixture
    def calculator(self):
        """Provide calculator instance"""
        return FinancialScenarioCalculator()
    
    def test_calculate_extra_payment_impact(self, calculator):
        """Test extra payment calculation"""
        result = calculator.calculate_extra_payment_impact(
            principal=10000,
            rate_annual=5.5,
            months=60,
            extra_payment=100
        )
        
        assert result['success'] is True
        assert 'savings' in result
        assert 'time_saved_months' in result
        assert result['savings'] > 0
        assert result['time_saved_months'] > 0
    
    def test_extra_payment_zero_rate(self, calculator):
        """Test extra payment with zero interest rate"""
        result = calculator.calculate_extra_payment_impact(
            principal=10000,
            rate_annual=0.0,
            months=60,
            extra_payment=50
        )
        
        assert result['success'] is True
        assert result['savings'] == 0  # No interest, no savings
    
    def test_compare_tenure_options(self, calculator):
        """Test tenure comparison"""
        result = calculator.compare_tenure_options(
            principal=10000,
            rate_annual=5.5,
            tenure_months_options=[36, 48, 60]
        )
        
        assert result['success'] is True
        assert 'options' in result
        assert len(result['options']) == 3
        
        # Verify shorter tenure has lower total cost
        assert result['options'][0]['total_payment'] < result['options'][2]['total_payment']
    
    def test_calculation_error_handling(self, calculator):
        """Test error handling in calculations"""
        # Test with invalid inputs
        result = calculator.calculate_extra_payment_impact(
            principal=-1000,  # Invalid
            rate_annual=5.5,
            months=60,
            extra_payment=100
        )
        
        # Should handle gracefully
        assert 'success' in result or 'error' in result


class TestFinancialAdvisorChatbot:
    """Test suite for FinancialAdvisorChatbot"""
    
    @pytest.fixture
    def chatbot(self):
        """Provide chatbot instance"""
        return FinancialAdvisorChatbot(use_llm=False)
    
    @pytest.fixture
    def sample_loan_data(self):
        """Provide sample loan data"""
        return {
            'principal_amount': 10000.00,
            'interest_rate': 5.5,
            'tenure_months': 60,
            'monthly_payment': 191.01,
            'bank_name': 'ABC Bank',
            'loan_type': 'education'
        }
    
    def test_ask_calculation_question(self, chatbot, sample_loan_data):
        """Test asking a calculation question"""
        response = chatbot.ask(
            question="What if I pay $100 extra per month?",
            document_id="doc123",
            structured_data=sample_loan_data
        )
        
        assert isinstance(response, ChatResponse)
        assert len(response.answer) > 0
        assert response.confidence > 0
        assert 'save' in response.answer.lower() or 'savings' in response.answer.lower()
    
    def test_ask_document_question(self, chatbot, sample_loan_data):
        """Test asking a document content question"""
        response = chatbot.ask(
            question="What happens if I miss a payment?",
            document_id="doc123",
            structured_data=sample_loan_data
        )
        
        assert isinstance(response, ChatResponse)
        assert len(response.answer) > 0
        assert 'late' in response.answer.lower() or 'payment' in response.answer.lower()
    
    def test_conversation_memory(self, chatbot, sample_loan_data):
        """Test conversation memory retention"""
        # First question
        chatbot.ask(
            "What is my interest rate?",
            "doc123",
            sample_loan_data
        )
        
        # Second question (follow-up)
        chatbot.ask(
            "Is that fixed or variable?",
            "doc123",
            sample_loan_data
        )
        
        history = chatbot.get_conversation_history()
        assert len(history) == 4  # 2 questions + 2 answers
    
    def test_extract_amount_from_question(self, chatbot):
        """Test amount extraction from questions"""
        assert chatbot._extract_amount_from_question("pay $100 extra") == 100.0
        assert chatbot._extract_amount_from_question("add 50 dollars") == 50.0
        assert chatbot._extract_amount_from_question("$1,000 more") == 1000.0
        assert chatbot._extract_amount_from_question("no amount here") is None
    
    def test_is_calculation_question(self, chatbot):
        """Test calculation question detection"""
        assert chatbot._is_calculation_question("What if I pay extra?") is True
        assert chatbot._is_calculation_question("How much will I save?") is True
        assert chatbot._is_calculation_question("What is APR?") is False
    
    def test_missing_structured_data(self, chatbot):
        """Test handling of missing structured data"""
        response = chatbot.ask(
            question="Calculate my savings",
            document_id="doc123",
            structured_data=None
        )
        
        assert isinstance(response, ChatResponse)
        assert 'need' in response.answer.lower() or 'missing' in response.answer.lower()
    
    def test_clear_conversation(self, chatbot, sample_loan_data):
        """Test clearing conversation history"""
        chatbot.ask("Test question", "doc123", sample_loan_data)
        assert len(chatbot.get_conversation_history()) > 0
        
        chatbot.clear_conversation()
        assert len(chatbot.get_conversation_history()) == 0
    
    def test_response_structure(self, chatbot, sample_loan_data):
        """Test that response has all required fields"""
        response = chatbot.ask(
            "What is my loan amount?",
            "doc123",
            sample_loan_data
        )
        
        assert hasattr(response, 'answer')
        assert hasattr(response, 'sources')
        assert hasattr(response, 'confidence')
        assert hasattr(response, 'context_used')
        assert hasattr(response, 'processing_time_ms')
    
    def test_error_handling(self, chatbot):
        """Test error handling for invalid inputs"""
        # Should not crash with empty question
        response = chatbot.ask("", "doc123", {})
        assert isinstance(response, ChatResponse)
    
    @pytest.mark.parametrize("question,expected_keyword", [
        ("What if I miss 3 payments?", "late"),
        ("Tell me about the interest rate", "rate"),
        ("Can I prepay?", "prepay"),
        ("How much extra should I pay?", "payment"),
    ])
    def test_common_questions(self, chatbot, sample_loan_data, question, expected_keyword):
        """Test responses to common questions contain relevant keywords"""
        response = chatbot.ask(question, "doc123", sample_loan_data)
        assert expected_keyword in response.answer.lower()


class TestChatResponse:
    """Test suite for ChatResponse dataclass"""
    
    def test_to_dict(self):
        """Test converting ChatResponse to dictionary"""
        response = ChatResponse(
            answer="Test answer",
            sources=[{'section': 'test'}],
            confidence=0.95,
            context_used=True,
            processing_time_ms=100.5
        )
        
        result = response.to_dict()
        assert isinstance(result, dict)
        assert result['answer'] == "Test answer"
        assert result['confidence'] == 0.95
        assert result['processing_time_ms'] == 100.5


class TestChatMessage:
    """Test suite for ChatMessage dataclass"""
    
    def test_message_creation(self):
        """Test creating a chat message"""
        msg = ChatMessage(
            role='user',
            content='Hello',
            timestamp=datetime.utcnow(),
            metadata={'test': 'data'}
        )
        
        assert msg.role == 'user'
        assert msg.content == 'Hello'
        assert isinstance(msg.timestamp, datetime)
        assert msg.metadata['test'] == 'data'


# Integration Tests
class TestChatbotIntegration:
    """Integration tests for complete chatbot workflows"""
    
    @pytest.fixture
    def chatbot(self):
        """Provide chatbot instance"""
        return FinancialAdvisorChatbot(use_llm=False)
    
    @pytest.fixture
    def full_loan_data(self):
        """Provide comprehensive loan data"""
        return {
            'principal_amount': 15000.00,
            'interest_rate': 6.5,
            'tenure_months': 48,
            'monthly_payment': 358.35,
            'bank_name': 'Education Bank',
            'loan_type': 'education',
            'processing_fee': 300.00
        }
    
    def test_multi_turn_conversation(self, chatbot, full_loan_data):
        """Test multi-turn conversation flow"""
        # Turn 1: Ask about loan
        r1 = chatbot.ask(
            "What is my monthly payment?",
            "doc123",
            full_loan_data
        )
        assert isinstance(r1, ChatResponse)
        
        # Turn 2: Follow-up calculation
        r2 = chatbot.ask(
            "What if I pay $50 extra?",
            "doc123",
            full_loan_data
        )
        assert isinstance(r2, ChatResponse)
        assert 'save' in r2.answer.lower()
        
        # Turn 3: Another question
        r3 = chatbot.ask(
            "Tell me about late payments",
            "doc123",
            full_loan_data
        )
        assert isinstance(r3, ChatResponse)
        
        # Verify all in history
        history = chatbot.get_conversation_history()
        assert len(history) == 6  # 3 questions + 3 answers
    
    def test_scenario_analysis_workflow(self, chatbot, full_loan_data):
        """Test complete scenario analysis workflow"""
        # Step 1: Get baseline
        r1 = chatbot.ask(
            "What are my loan details?",
            "doc123",
            full_loan_data
        )
        assert full_loan_data['monthly_payment'] or 'payment' in r1.answer.lower()
        
        # Step 2: Analyze extra payment
        r2 = chatbot.ask(
            "What if I pay $100 extra per month?",
            "doc123",
            full_loan_data
        )
        assert 'save' in r2.answer.lower()
        
        # Step 3: Compare tenures
        r3 = chatbot.ask(
            "Compare 36 vs 48 month terms",
            "doc123",
            full_loan_data
        )
        assert 'month' in r3.answer.lower()
