"""
Tests for Financial Education Service

"""

import pytest
from src.api.services.financial_education import (
    FinancialEducationService,
    FinancialGlossary,
    ScenarioSimulator,
    BestPracticesLibrary,
    FinancialTerm,
    ScenarioResult,
    BestPractice
)


class TestFinancialGlossary:
    """Test suite for FinancialGlossary"""
    
    def test_get_term_exists(self):
        """Test retrieving an existing term"""
        term = FinancialGlossary.get_term('APR')
        
        assert term is not None
        assert term.term == 'APR (Annual Percentage Rate)'
        assert term.simple_explanation
        assert term.example
    
    def test_get_term_case_insensitive(self):
        """Test case-insensitive term retrieval"""
        term1 = FinancialGlossary.get_term('apr')
        term2 = FinancialGlossary.get_term('APR')
        term3 = FinancialGlossary.get_term('Apr')
        
        assert term1 is not None
        assert term1.term == term2.term == term3.term
    
    def test_get_term_not_found(self):
        """Test retrieving non-existent term"""
        term = FinancialGlossary.get_term('NonExistentTerm')
        assert term is None
    
    def test_search_terms(self):
        """Test searching for terms"""
        results = FinancialGlossary.search_terms('interest')
        
        assert len(results) > 0
        assert any('interest' in r.term.lower() or 'interest' in r.simple_explanation.lower() 
                  for r in results)
    
    def test_get_all_terms(self):
        """Test getting all terms"""
        all_terms = FinancialGlossary.get_all_terms()
        
        assert len(all_terms) > 0
        assert all(isinstance(t, FinancialTerm) for t in all_terms)
    
    def test_get_terms_by_category(self):
        """Test filtering terms by category"""
        terms = FinancialGlossary.get_all_terms(category='Interest & Rates')
        
        assert len(terms) > 0
        assert all(t.category == 'Interest & Rates' for t in terms)
    
    def test_get_categories(self):
        """Test getting all categories"""
        categories = FinancialGlossary.get_categories()
        
        assert len(categories) > 0
        assert 'Interest & Rates' in categories
        assert 'Loan Basics' in categories
    
    def test_term_has_translations(self):
        """Test that terms have multilingual translations"""
        term = FinancialGlossary.get_term('Principal')
        
        assert 'hi' in term.translations
        assert 'te' in term.translations
        assert 'ta' in term.translations


class TestScenarioSimulator:
    """Test suite for ScenarioSimulator"""
    
    @pytest.fixture
    def simulator(self):
        """Provide simulator instance"""
        return ScenarioSimulator()
    
    def test_simulate_extra_payment(self, simulator):
        """Test extra payment simulation"""
        result = simulator.simulate_extra_payment(
            principal=10000,
            rate_annual=5.5,
            months=60,
            extra_payment=100
        )
        
        assert isinstance(result, ScenarioResult)
        assert result.scenario_type == 'extra_payment'
        assert result.outputs['savings'] > 0
        assert result.outputs['time_saved_months'] > 0
        assert result.outputs['new_tenure_months'] < 60
    
    def test_extra_payment_reduces_total_cost(self, simulator):
        """Test that extra payment reduces total cost"""
        result = simulator.simulate_extra_payment(
            principal=10000,
            rate_annual=6.0,
            months=60,
            extra_payment=50
        )
        
        regular_total = result.outputs['regular_total']
        new_total = result.outputs['new_total']
        
        assert new_total < regular_total
        assert result.outputs['savings'] == regular_total - new_total
    
    def test_extra_payment_zero_interest(self, simulator):
        """Test extra payment with zero interest rate"""
        result = simulator.simulate_extra_payment(
            principal=10000,
            rate_annual=0.0,
            months=60,
            extra_payment=50
        )
        
        assert isinstance(result, ScenarioResult)
        assert result.outputs['new_tenure_months'] < 60
    
    def test_compare_loan_tenures(self, simulator):
        """Test tenure comparison"""
        result = simulator.compare_loan_tenures(
            principal=10000,
            rate_annual=5.5,
            tenure_options=[36, 48, 60]
        )
        
        assert isinstance(result, ScenarioResult)
        assert result.scenario_type == 'tenure_comparison'
        assert len(result.outputs['comparisons']) == 3
        
        # Verify shorter tenure has lower total cost
        comparisons = result.outputs['comparisons']
        assert comparisons[0]['total_payment'] < comparisons[2]['total_payment']
        # But higher monthly payment
        assert comparisons[0]['monthly_payment'] > comparisons[2]['monthly_payment']
    
    def test_tenure_comparison_best_option(self, simulator):
        """Test that best option is identified correctly"""
        result = simulator.compare_loan_tenures(
            principal=15000,
            rate_annual=6.5,
            tenure_options=[24, 36, 48, 60]
        )
        
        best = result.outputs['best_option']
        assert 'tenure_months' in best
        assert 'total_payment' in best
        
        # Best option should be shortest tenure (lowest total cost)
        assert best['tenure_months'] == 24
    
    def test_scenario_result_to_dict(self, simulator):
        """Test converting scenario result to dictionary"""
        result = simulator.simulate_extra_payment(
            principal=10000,
            rate_annual=5.0,
            months=60,
            extra_payment=75
        )
        
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert 'scenario_type' in result_dict
        assert 'inputs' in result_dict
        assert 'outputs' in result_dict
        assert 'explanation' in result_dict


class TestBestPracticesLibrary:
    """Test suite for BestPracticesLibrary"""
    
    def test_get_all_practices(self):
        """Test getting all best practices"""
        practices = BestPracticesLibrary.get_all_practices()
        
        assert len(practices) > 0
        assert all(isinstance(p, BestPractice) for p in practices)
    
    def test_filter_by_category(self):
        """Test filtering practices by category"""
        practices = BestPracticesLibrary.get_all_practices(category='Financial Safety')
        
        assert len(practices) > 0
        assert all(p.category == 'Financial Safety' for p in practices)
    
    def test_filter_by_applicable_to(self):
        """Test filtering practices by applicability"""
        practices = BestPracticesLibrary.get_all_practices(applicable_to='student')
        
        assert len(practices) > 0
        assert all('student' in p.applicable_to or 'all' in p.applicable_to 
                  for p in practices)
    
    def test_filter_by_importance(self):
        """Test filtering practices by importance"""
        practices = BestPracticesLibrary.get_all_practices(importance='high')
        
        assert len(practices) > 0
        assert all(p.importance == 'high' for p in practices)
    
    def test_get_categories(self):
        """Test getting practice categories"""
        categories = BestPracticesLibrary.get_categories()
        
        assert len(categories) > 0
        assert isinstance(categories, list)
    
    def test_practice_has_action_items(self):
        """Test that practices include actionable items"""
        practices = BestPracticesLibrary.get_all_practices()
        
        for practice in practices:
            assert len(practice.action_items) > 0


class TestFinancialEducationService:
    """Test suite for FinancialEducationService"""
    
    @pytest.fixture
    def service(self):
        """Provide financial education service"""
        return FinancialEducationService()
    
    def test_explain_term_found(self, service):
        """Test explaining an existing term"""
        result = service.explain_term('APR')
        
        assert result['found'] is True
        assert 'term' in result
        assert result['term']['term']
    
    def test_explain_term_not_found(self, service):
        """Test explaining non-existent term"""
        result = service.explain_term('FakeTermXYZ')
        
        assert result['found'] is False
        assert 'suggestions' in result
    
    def test_explain_term_with_related(self, service):
        """Test explaining term with related terms"""
        result = service.explain_term('APR', include_related=True)
        
        assert result['found'] is True
        if 'related_terms' in result:
            assert isinstance(result['related_terms'], list)
    
    def test_search_glossary(self, service):
        """Test searching glossary"""
        results = service.search_glossary('payment')
        
        assert isinstance(results, list)
        assert len(results) > 0
    
    def test_get_all_terms(self, service):
        """Test getting all terms"""
        terms = service.get_all_terms()
        
        assert isinstance(terms, list)
        assert len(terms) > 0
        assert all(isinstance(t, dict) for t in terms)
    
    def test_get_terms_by_category(self, service):
        """Test getting terms filtered by category"""
        terms = service.get_all_terms(category='Payments')
        
        assert isinstance(terms, list)
        if len(terms) > 0:
            assert all(t['category'] == 'Payments' for t in terms)
    
    def test_simulate_extra_payment_scenario(self, service):
        """Test simulating extra payment scenario"""
        result = service.simulate_scenario(
            scenario_type='extra_payment',
            params={
                'principal': 10000,
                'rate_annual': 5.5,
                'months': 60,
                'extra_payment': 100
            }
        )
        
        assert result['success'] is True
        assert 'result' in result
        assert result['result']['outputs']['savings'] > 0
    
    def test_simulate_tenure_comparison_scenario(self, service):
        """Test simulating tenure comparison"""
        result = service.simulate_scenario(
            scenario_type='tenure_comparison',
            params={
                'principal': 15000,
                'rate_annual': 6.0,
                'tenure_options': [36, 48, 60]
            }
        )
        
        assert result['success'] is True
        assert 'result' in result
        assert len(result['result']['outputs']['comparisons']) == 3
    
    def test_simulate_invalid_scenario_type(self, service):
        """Test simulating with invalid scenario type"""
        result = service.simulate_scenario(
            scenario_type='invalid_type',
            params={}
        )
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_get_best_practices_no_filter(self, service):
        """Test getting best practices without filters"""
        practices = service.get_best_practices()
        
        assert isinstance(practices, list)
        assert len(practices) > 0
        assert all(isinstance(p, dict) for p in practices)
    
    def test_get_best_practices_for_student(self, service):
        """Test getting best practices for students"""
        practices = service.get_best_practices(
            user_profile={'role': 'student'}
        )
        
        assert isinstance(practices, list)
        assert len(practices) > 0
    
    def test_get_best_practices_for_parent(self, service):
        """Test getting best practices for parents"""
        practices = service.get_best_practices(
            user_profile={'role': 'parent'}
        )
        
        assert isinstance(practices, list)
        assert len(practices) > 0
    
    def test_get_best_practices_high_importance(self, service):
        """Test getting high importance practices"""
        practices = service.get_best_practices(
            user_profile={'importance': 'high'}
        )
        
        assert isinstance(practices, list)
        assert all(p['importance'] == 'high' for p in practices)
    
    def test_get_learning_path_student(self, service):
        """Test getting student learning path"""
        path = service.get_learning_path(user_type='student')
        
        assert 'title' in path
        assert 'modules' in path
        assert len(path['modules']) > 0
        assert 'total_time' in path
    
    def test_get_learning_path_parent(self, service):
        """Test getting parent learning path"""
        path = service.get_learning_path(user_type='parent')
        
        assert 'title' in path
        assert 'modules' in path
        assert len(path['modules']) > 0
        assert 'total_time' in path
        
        # Parent path should be shorter
        student_path = service.get_learning_path('student')
        assert len(path['modules']) <= len(student_path['modules'])


class TestFinancialTerm:
    """Test suite for FinancialTerm dataclass"""
    
    def test_term_to_dict(self):
        """Test converting term to dictionary"""
        term = FinancialTerm(
            term='Test Term',
            category='Test',
            simple_explanation='Simple',
            detailed_explanation='Detailed',
            example='Example',
            why_it_matters='Matters',
            related_terms=['Related'],
            translations={'hi': 'टेस्ट'}
        )
        
        term_dict = term.to_dict()
        assert isinstance(term_dict, dict)
        assert term_dict['term'] == 'Test Term'
        assert 'translations' in term_dict


class TestBestPractice:
    """Test suite for BestPractice dataclass"""
    
    def test_practice_to_dict(self):
        """Test converting practice to dictionary"""
        practice = BestPractice(
            title='Test Practice',
            category='Test',
            description='Description',
            importance='high',
            applicable_to=['student'],
            action_items=['Action 1', 'Action 2']
        )
        
        practice_dict = practice.to_dict()
        assert isinstance(practice_dict, dict)
        assert practice_dict['title'] == 'Test Practice'
        assert len(practice_dict['action_items']) == 2


# Integration Tests
class TestFinancialEducationIntegration:
    """Integration tests for financial education service"""
    
    @pytest.fixture
    def service(self):
        """Provide service instance"""
        return FinancialEducationService()
    
    def test_complete_learning_workflow(self, service):
        """Test complete learning workflow"""
        # Step 1: Get learning path
        path = service.get_learning_path('student')
        assert 'modules' in path
        
        # Step 2: Learn terms from first module
        first_module = path['modules'][0]
        for topic in first_module['topics']:
            result = service.explain_term(topic)
            if result['found']:
                assert result['term']['simple_explanation']
        
        # Step 3: Run scenario simulations
        scenario = service.simulate_scenario(
            'extra_payment',
            {
                'principal': 10000,
                'rate_annual': 6.0,
                'months': 60,
                'extra_payment': 50
            }
        )
        assert scenario['success']
        
        # Step 4: Get best practices
        practices = service.get_best_practices({'role': 'student'})
        assert len(practices) > 0
    
    def test_realistic_student_scenario(self, service):
        """Test realistic student loan scenario"""
        # Student has $15,000 loan at 6.5% for 48 months
        # Wants to know impact of $100 extra payment
        
        result = service.simulate_scenario(
            'extra_payment',
            {
                'principal': 15000,
                'rate_annual': 6.5,
                'months': 48,
                'extra_payment': 100
            }
        )
        
        assert result['success']
        outputs = result['result']['outputs']
        
        # Should see significant savings
        assert outputs['savings'] > 500
        assert outputs['time_saved_months'] > 5
        
        # Check explanation is helpful
        explanation = result['result']['explanation']
        assert 'save' in explanation.lower()
        assert '$' in explanation
    
    @pytest.mark.parametrize("term,expected_category", [
        ('APR', 'Interest & Rates'),
        ('Principal', 'Loan Basics'),
        ('EMI', 'Payments'),
        ('Default', 'Risks'),
    ])
    def test_term_categories(self, service, term, expected_category):
        """Test that terms are in correct categories"""
        result = service.explain_term(term)
        assert result['found']
        assert result['term']['category'] == expected_category
