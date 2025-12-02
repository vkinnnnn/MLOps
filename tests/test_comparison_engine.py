"""
Tests for Comparison Engine
Following KIRO Global Steering Guidelines
"""

import pytest
from src.api.services.comparison_engine import (
    LoanComparisonEngine,
    LoanMetrics,
    FlexibilityScore,
    ProsCons,
    ComparisonResult
)


class TestLoanComparisonEngine:
    """Test suite for LoanComparisonEngine"""
    
    @pytest.fixture
    def engine(self):
        """Provide comparison engine instance"""
        return LoanComparisonEngine(use_ai=False)
    
    @pytest.fixture
    def sample_loans(self):
        """Provide sample loan data"""
        return [
            {
                'document_id': 'loan1',
                'document_name': 'Bank A Loan',
                'normalized_data': {
                    'principal_amount': 10000.00,
                    'interest_rate': 5.5,
                    'tenure_months': 60,
                    'monthly_payment': 191.01,
                    'bank_name': 'Bank A',
                    'loan_type': 'education',
                    'processing_fee': 200.00,
                    'other_fees': 50.00
                },
                'complete_extraction': {
                    'text_extraction': {
                        'all_text': 'No prepayment penalty. Deferment available for 6 months.'
                    }
                }
            },
            {
                'document_id': 'loan2',
                'document_name': 'Bank B Loan',
                'normalized_data': {
                    'principal_amount': 10000.00,
                    'interest_rate': 6.5,
                    'tenure_months': 48,
                    'monthly_payment': 237.90,
                    'bank_name': 'Bank B',
                    'loan_type': 'education',
                    'processing_fee': 100.00,
                    'other_fees': 0.00
                },
                'complete_extraction': {
                    'text_extraction': {
                        'all_text': 'Prepayment penalty applies. No deferment options.'
                    }
                }
            },
            {
                'document_id': 'loan3',
                'document_name': 'Bank C Loan',
                'normalized_data': {
                    'principal_amount': 10000.00,
                    'interest_rate': 5.0,
                    'tenure_months': 72,
                    'monthly_payment': 161.33,
                    'bank_name': 'Bank C',
                    'loan_type': 'education',
                    'processing_fee': 300.00,
                    'other_fees': 100.00
                },
                'complete_extraction': {
                    'text_extraction': {
                        'all_text': 'Flexible payment dates. Top-up facility available.'
                    }
                }
            }
        ]
    
    def test_compare_loans_success(self, engine, sample_loans):
        """Test successful loan comparison"""
        result = engine.compare_loans(sample_loans)
        
        assert isinstance(result, ComparisonResult)
        assert len(result.metrics) == 3
        assert len(result.flexibility_scores) == 3
        assert len(result.pros_cons) == 3
        assert result.best_overall
        assert result.best_by_category
        assert result.recommendation
    
    def test_compare_loans_empty_list(self, engine):
        """Test comparison with empty loans list"""
        with pytest.raises(ValueError, match="At least one loan is required"):
            engine.compare_loans([])
    
    def test_compare_single_loan(self, engine, sample_loans):
        """Test comparison with single loan (should work with warning)"""
        result = engine.compare_loans([sample_loans[0]])
        
        assert isinstance(result, ComparisonResult)
        assert len(result.metrics) == 1
    
    def test_calculate_metrics(self, engine, sample_loans):
        """Test metrics calculation"""
        metrics = engine._calculate_metrics(sample_loans)
        
        assert len(metrics) == 3
        assert all(isinstance(m, LoanMetrics) for m in metrics)
        
        # Check first loan metrics
        m1 = metrics[0]
        assert m1.principal == 10000.00
        assert m1.interest_rate == 5.5
        assert m1.tenure_months == 60
        assert m1.monthly_payment == 191.01
        assert m1.total_cost == pytest.approx(191.01 * 60, rel=0.01)
        assert m1.processing_fee == 200.00
        assert m1.upfront_costs == 250.00
    
    def test_score_flexibility(self, engine, sample_loans):
        """Test flexibility scoring"""
        scores = engine._score_flexibility(sample_loans)
        
        assert len(scores) == 3
        assert all(isinstance(s, FlexibilityScore) for s in scores)
        
        # Loan 1 should have high flexibility (no prepayment penalty, deferment)
        assert scores[0].score >= 4
        assert 'prepayment' in ' '.join(scores[0].features).lower()
        
        # Loan 2 should have low flexibility
        assert scores[1].score < scores[0].score
        
        # All scores should be 0-10
        assert all(0 <= s.score <= 10 for s in scores)
    
    def test_generate_pros_cons(self, engine, sample_loans):
        """Test pros/cons generation"""
        metrics = engine._calculate_metrics(sample_loans)
        flexibility = engine._score_flexibility(sample_loans)
        pros_cons = engine._generate_pros_cons(sample_loans, metrics, flexibility)
        
        assert len(pros_cons) == 3
        assert all(isinstance(pc, ProsCons) for pc in pros_cons)
        
        # Each should have pros and cons
        for pc in pros_cons:
            assert len(pc.pros) > 0 or len(pc.cons) > 0
            assert pc.summary
    
    def test_find_best_by_category(self, engine, sample_loans):
        """Test finding best loans by category"""
        metrics = engine._calculate_metrics(sample_loans)
        flexibility = engine._score_flexibility(sample_loans)
        best = engine._find_best_by_category(metrics, flexibility)
        
        assert 'lowest_total_cost' in best
        assert 'lowest_monthly_payment' in best
        assert 'lowest_interest_rate' in best
        assert 'most_flexible' in best
        assert 'lowest_upfront_costs' in best
    
    def test_generate_recommendation(self, engine, sample_loans):
        """Test recommendation generation"""
        metrics = engine._calculate_metrics(sample_loans)
        flexibility = engine._score_flexibility(sample_loans)
        pros_cons = engine._generate_pros_cons(sample_loans, metrics, flexibility)
        best_by_cat = engine._find_best_by_category(metrics, flexibility)
        
        recommendation = engine._generate_recommendation(
            sample_loans, metrics, flexibility, pros_cons, best_by_cat
        )
        
        assert isinstance(recommendation, str)
        assert len(recommendation) > 100  # Should be substantial
        assert 'recommendation' in recommendation.lower() or 'best' in recommendation.lower()
    
    def test_metrics_to_dict(self, engine, sample_loans):
        """Test LoanMetrics conversion to dictionary"""
        metrics = engine._calculate_metrics(sample_loans)
        metric_dict = metrics[0].to_dict()
        
        assert isinstance(metric_dict, dict)
        assert 'loan_id' in metric_dict
        assert 'bank_name' in metric_dict
        assert 'principal' in metric_dict
        assert 'total_cost' in metric_dict
    
    def test_comparison_result_to_dict(self, engine, sample_loans):
        """Test ComparisonResult conversion to dictionary"""
        result = engine.compare_loans(sample_loans)
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert 'loans' in result_dict
        assert 'metrics' in result_dict
        assert 'flexibility_scores' in result_dict
        assert 'pros_cons' in result_dict
        assert 'best_overall' in result_dict
        assert 'recommendation' in result_dict
    
    def test_effective_rate_calculation(self, engine):
        """Test effective rate calculation"""
        effective = engine._calculate_effective_rate(
            principal=10000,
            nominal_rate=10.0,
            months=60,
            fees=500
        )
        
        # Effective rate should be higher than nominal due to fees
        assert effective > 10.0
    
    def test_has_feature_detection(self, engine):
        """Test feature detection in text"""
        text = "no prepayment penalty and flexible payment dates"
        
        assert engine._has_feature(text, ['prepayment'])
        assert engine._has_feature(text, ['flexible'])
        assert not engine._has_feature(text, ['collateral'])
    
    @pytest.mark.parametrize("loan_count,expected_comparisons", [
        (2, 2),
        (3, 3),
        (5, 5),
    ])
    def test_multiple_loan_counts(self, engine, sample_loans, loan_count, expected_comparisons):
        """Test comparison with different numbers of loans"""
        loans = sample_loans[:loan_count]
        result = engine.compare_loans(loans)
        
        assert len(result.metrics) == expected_comparisons
        assert len(result.flexibility_scores) == expected_comparisons


class TestFlexibilityScore:
    """Test suite for FlexibilityScore"""
    
    def test_flexibility_score_creation(self):
        """Test creating a flexibility score"""
        score = FlexibilityScore(
            loan_id='loan1',
            bank_name='Test Bank',
            score=8,
            features=['No prepayment penalty', 'Deferment'],
            details={'prepayment_allowed': True}
        )
        
        assert score.score == 8
        assert len(score.features) == 2
        assert score.details['prepayment_allowed'] is True
    
    def test_flexibility_score_to_dict(self):
        """Test converting flexibility score to dictionary"""
        score = FlexibilityScore(
            loan_id='loan1',
            bank_name='Test Bank',
            score=7,
            features=['Feature 1'],
            details={'test': True}
        )
        
        score_dict = score.to_dict()
        assert isinstance(score_dict, dict)
        assert score_dict['score'] == 7


class TestProsCons:
    """Test suite for ProsCons"""
    
    def test_pros_cons_creation(self):
        """Test creating pros/cons"""
        pc = ProsCons(
            loan_id='loan1',
            bank_name='Test Bank',
            pros=['Low rate', 'Flexible'],
            cons=['High fees'],
            summary='Good option overall'
        )
        
        assert len(pc.pros) == 2
        assert len(pc.cons) == 1
        assert pc.summary
    
    def test_pros_cons_to_dict(self):
        """Test converting pros/cons to dictionary"""
        pc = ProsCons(
            loan_id='loan1',
            bank_name='Test Bank',
            pros=['Pro 1'],
            cons=['Con 1'],
            summary='Summary'
        )
        
        pc_dict = pc.to_dict()
        assert isinstance(pc_dict, dict)
        assert 'pros' in pc_dict
        assert 'cons' in pc_dict


# Integration Tests
class TestComparisonEngineIntegration:
    """Integration tests for comparison engine"""
    
    @pytest.fixture
    def engine(self):
        """Provide comparison engine"""
        return LoanComparisonEngine()
    
    @pytest.fixture
    def realistic_loans(self):
        """Provide realistic loan scenarios"""
        return [
            {
                'document_id': 'edu_loan_a',
                'document_name': 'Education Loan - University Bank',
                'normalized_data': {
                    'principal_amount': 15000.00,
                    'interest_rate': 6.5,
                    'tenure_months': 48,
                    'monthly_payment': 358.35,
                    'bank_name': 'University Bank',
                    'loan_type': 'education',
                    'processing_fee': 300.00,
                    'other_fees': 100.00
                },
                'complete_extraction': {
                    'text_extraction': {
                        'all_text': '''Education loan agreement. No prepayment penalty. 
                        Grace period of 6 months after graduation. Deferment available 
                        in case of financial hardship. Flexible payment dates.'''
                    }
                }
            },
            {
                'document_id': 'edu_loan_b',
                'document_name': 'Student Loan - National Bank',
                'normalized_data': {
                    'principal_amount': 15000.00,
                    'interest_rate': 5.5,
                    'tenure_months': 60,
                    'monthly_payment': 286.51,
                    'bank_name': 'National Bank',
                    'loan_type': 'education',
                    'processing_fee': 450.00,
                    'other_fees': 0.00
                },
                'complete_extraction': {
                    'text_extraction': {
                        'all_text': '''Student loan terms. Prepayment penalty of 2%. 
                        No grace period. Standard payment schedule only.'''
                    }
                }
            }
        ]
    
    def test_realistic_comparison(self, engine, realistic_loans):
        """Test comparison with realistic loan data"""
        result = engine.compare_loans(realistic_loans)
        
        # Verify complete result structure
        assert result.best_overall
        assert result.recommendation
        assert len(result.metrics) == 2
        
        # Verify metrics make sense
        for metric in result.metrics:
            assert metric.total_cost > metric.principal
            assert metric.total_interest > 0
            assert metric.monthly_payment > 0
        
        # Verify flexibility scoring worked
        for flex in result.flexibility_scores:
            assert 0 <= flex.score <= 10
        
        # University Bank should have higher flexibility (no penalty, grace period)
        uni_bank_flex = next(f for f in result.flexibility_scores if f.bank_name == 'University Bank')
        nat_bank_flex = next(f for f in result.flexibility_scores if f.bank_name == 'National Bank')
        assert uni_bank_flex.score > nat_bank_flex.score
    
    def test_edge_case_zero_fees(self, engine):
        """Test loan with zero fees"""
        loan = {
            'document_id': 'test',
            'normalized_data': {
                'principal_amount': 10000,
                'interest_rate': 5.0,
                'tenure_months': 60,
                'monthly_payment': 188.71,
                'bank_name': 'Test Bank',
                'processing_fee': 0,
                'other_fees': 0
            },
            'complete_extraction': {
                'text_extraction': {'all_text': ''}
            }
        }
        
        result = engine.compare_loans([loan])
        assert result.metrics[0].upfront_costs == 0
    
    def test_edge_case_very_short_tenure(self, engine):
        """Test loan with very short tenure"""
        loan = {
            'document_id': 'test',
            'normalized_data': {
                'principal_amount': 5000,
                'interest_rate': 8.0,
                'tenure_months': 12,
                'monthly_payment': 434.59,
                'bank_name': 'Quick Bank',
                'processing_fee': 100,
                'other_fees': 0
            },
            'complete_extraction': {
                'text_extraction': {'all_text': ''}
            }
        }
        
        result = engine.compare_loans([loan])
        assert result.metrics[0].tenure_months == 12
        # Should note short tenure in pros/cons
        pc = result.pros_cons[0]
        assert any('short' in p.lower() or 'quick' in p.lower() for p in pc.pros)
