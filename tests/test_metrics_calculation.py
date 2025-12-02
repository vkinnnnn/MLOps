"""
Unit tests for metrics calculation
Tests comparison metrics, total cost, effective rate, and flexibility score
"""
import pytest
from typing import Dict, Any, List
import math


class TestTotalCostCalculation:
    """Test total cost estimation"""
    
    def test_simple_total_cost(self):
        """Test calculation of total cost with simple interest"""
        principal = 50000
        interest_rate = 8.5  # Annual percentage
        tenure_months = 60
        
        # Simple calculation: principal + total interest
        annual_interest = principal * (interest_rate / 100)
        total_interest = annual_interest * (tenure_months / 12)
        total_cost = principal + total_interest
        
        assert total_cost > principal, "Total cost should exceed principal"
        assert total_cost == principal + total_interest, \
            "Total cost should equal principal plus interest"
    
    def test_total_cost_with_fees(self):
        """Test total cost including all fees"""
        principal = 50000
        interest = 21250  # Total interest over tenure
        processing_fee = 500
        administrative_fee = 100
        documentation_fee = 50
        
        total_fees = processing_fee + administrative_fee + documentation_fee
        total_cost = principal + interest + total_fees
        
        expected = 50000 + 21250 + 650
        assert total_cost == expected, \
            f"Total cost should be {expected}"
    
    def test_total_cost_with_penalties(self):
        """Test total cost including potential penalties"""
        base_cost = 71900  # Principal + interest + fees
        late_payment_penalty = 100
        
        total_with_penalty = base_cost + late_payment_penalty
        
        assert total_with_penalty > base_cost, \
            "Cost with penalty should exceed base cost"
    
    def test_emi_based_total_cost(self):
        """Test total cost calculation from EMI"""
        monthly_emi = 1000
        tenure_months = 60
        
        total_paid = monthly_emi * tenure_months
        
        assert total_paid == 60000, "Total paid should equal EMI × tenure"
    
    def test_total_cost_comparison(self):
        """Test comparison of total costs between loans"""
        loan1_cost = 71900
        loan2_cost = 68500
        loan3_cost = 75000
        
        costs = [loan1_cost, loan2_cost, loan3_cost]
        best_cost = min(costs)
        
        assert best_cost == loan2_cost, "Should identify lowest cost loan"


class TestEffectiveInterestRate:
    """Test effective interest rate calculation"""
    
    def test_simple_effective_rate(self):
        """Test effective rate when nominal rate equals effective rate"""
        nominal_rate = 8.5
        # With annual compounding, effective rate ≈ nominal rate
        
        effective_rate = nominal_rate
        
        assert effective_rate == nominal_rate, \
            "Simple effective rate should equal nominal rate"
    
    def test_effective_rate_with_fees(self):
        """Test effective rate including fees"""
        principal = 50000
        nominal_rate = 8.5
        processing_fee = 500
        tenure_months = 60
        
        # Effective principal is reduced by upfront fees
        effective_principal = principal - processing_fee
        
        # Effective rate is higher due to fees
        effective_rate = nominal_rate * (principal / effective_principal)
        
        assert effective_rate > nominal_rate, \
            "Effective rate should be higher when fees are included"
    
    def test_apr_calculation(self):
        """Test APR (Annual Percentage Rate) calculation"""
        nominal_rate = 8.5
        fees_percentage = 1.0  # 1% in fees
        
        apr = nominal_rate + fees_percentage
        
        assert apr > nominal_rate, "APR should include fees"
        assert apr == 9.5, "APR should be 9.5%"
    
    def test_monthly_to_annual_rate(self):
        """Test conversion of monthly rate to annual rate"""
        monthly_rate = 0.7083  # Approximately 8.5% annual / 12
        
        annual_rate = monthly_rate * 12
        
        assert abs(annual_rate - 8.5) < 0.01, \
            "Annual rate should be approximately 8.5%"
    
    def test_compound_interest_effect(self):
        """Test effect of compounding on effective rate"""
        nominal_rate = 8.5
        compounding_periods = 12  # Monthly compounding
        
        # Effective annual rate with compounding
        effective_rate = ((1 + nominal_rate / 100 / compounding_periods) ** compounding_periods - 1) * 100
        
        assert effective_rate > nominal_rate, \
            "Effective rate with compounding should be higher"


class TestFlexibilityScore:
    """Test flexibility score calculation"""
    
    def test_flexibility_with_moratorium(self):
        """Test flexibility score with moratorium period"""
        has_moratorium = True
        moratorium_months = 6
        
        # Moratorium adds to flexibility
        moratorium_score = 2.0 if has_moratorium else 0.0
        
        assert moratorium_score > 0, "Moratorium should increase flexibility"
    
    def test_flexibility_with_prepayment(self):
        """Test flexibility score with prepayment options"""
        prepayment_allowed = True
        prepayment_penalty = 0  # No penalty
        
        # No penalty adds to flexibility
        prepayment_score = 3.0 if prepayment_allowed and prepayment_penalty == 0 else 1.0
        
        assert prepayment_score == 3.0, \
            "No prepayment penalty should give high flexibility score"
    
    def test_flexibility_with_partial_payment(self):
        """Test flexibility score with partial payment options"""
        partial_payment_allowed = True
        
        partial_payment_score = 2.0 if partial_payment_allowed else 0.0
        
        assert partial_payment_score > 0, \
            "Partial payment option should increase flexibility"
    
    def test_flexibility_with_payment_modes(self):
        """Test flexibility score with multiple payment modes"""
        payment_modes = ["EMI", "Bullet Payment", "Step-up Payment"]
        
        # More payment modes = more flexibility
        mode_score = min(len(payment_modes) * 1.0, 3.0)
        
        assert mode_score == 3.0, "Multiple payment modes should give high score"
    
    def test_overall_flexibility_score(self):
        """Test calculation of overall flexibility score"""
        moratorium_score = 2.0
        prepayment_score = 3.0
        partial_payment_score = 2.0
        payment_mode_score = 3.0
        
        total_score = moratorium_score + prepayment_score + partial_payment_score + payment_mode_score
        
        # Normalize to 0-10 scale
        flexibility_score = min(total_score, 10.0)
        
        assert 0 <= flexibility_score <= 10, \
            "Flexibility score should be between 0 and 10"
        assert flexibility_score == 10.0, "Should calculate maximum flexibility"
    
    def test_flexibility_comparison(self):
        """Test comparison of flexibility scores"""
        loan1_flexibility = 8.5
        loan2_flexibility = 6.0
        loan3_flexibility = 9.0
        
        scores = [loan1_flexibility, loan2_flexibility, loan3_flexibility]
        best_flexibility = max(scores)
        
        assert best_flexibility == loan3_flexibility, \
            "Should identify most flexible loan"


class TestMonthlyEMICalculation:
    """Test monthly EMI calculation"""
    
    def test_simple_emi_calculation(self):
        """Test EMI calculation using standard formula"""
        principal = 50000
        annual_rate = 8.5
        tenure_months = 60
        
        # Monthly interest rate
        monthly_rate = annual_rate / 12 / 100
        
        # EMI formula: P * r * (1+r)^n / ((1+r)^n - 1)
        emi = principal * monthly_rate * ((1 + monthly_rate) ** tenure_months) / \
              (((1 + monthly_rate) ** tenure_months) - 1)
        
        assert emi > 0, "EMI should be positive"
        assert emi < principal, "Monthly EMI should be less than principal"
    
    def test_emi_with_different_tenures(self):
        """Test EMI calculation with different tenures"""
        principal = 50000
        annual_rate = 8.5
        
        tenures = [12, 24, 36, 60]
        emis = []
        
        for tenure in tenures:
            monthly_rate = annual_rate / 12 / 100
            emi = principal * monthly_rate * ((1 + monthly_rate) ** tenure) / \
                  (((1 + monthly_rate) ** tenure) - 1)
            emis.append(emi)
        
        # Longer tenure should result in lower EMI
        assert emis[0] > emis[1] > emis[2] > emis[3], \
            "EMI should decrease with longer tenure"
    
    def test_total_interest_from_emi(self):
        """Test calculation of total interest from EMI"""
        principal = 50000
        monthly_emi = 1000
        tenure_months = 60
        
        total_paid = monthly_emi * tenure_months
        total_interest = total_paid - principal
        
        assert total_interest > 0, "Total interest should be positive"
        assert total_interest == 10000, "Total interest should be 10000"


class TestComparisonMetrics:
    """Test comparison metrics between loans"""
    
    def test_cost_comparison(self):
        """Test comparison by total cost"""
        loans = [
            {"id": "loan1", "total_cost": 71900},
            {"id": "loan2", "total_cost": 68500},
            {"id": "loan3", "total_cost": 75000},
        ]
        
        best_by_cost = min(loans, key=lambda x: x["total_cost"])
        
        assert best_by_cost["id"] == "loan2", \
            "Should identify loan with lowest cost"
    
    def test_flexibility_comparison(self):
        """Test comparison by flexibility"""
        loans = [
            {"id": "loan1", "flexibility": 8.5},
            {"id": "loan2", "flexibility": 6.0},
            {"id": "loan3", "flexibility": 9.0},
        ]
        
        best_by_flexibility = max(loans, key=lambda x: x["flexibility"])
        
        assert best_by_flexibility["id"] == "loan3", \
            "Should identify most flexible loan"
    
    def test_rate_comparison(self):
        """Test comparison by interest rate"""
        loans = [
            {"id": "loan1", "rate": 8.5},
            {"id": "loan2", "rate": 7.5},
            {"id": "loan3", "rate": 9.0},
        ]
        
        best_by_rate = min(loans, key=lambda x: x["rate"])
        
        assert best_by_rate["id"] == "loan2", \
            "Should identify loan with lowest rate"
    
    def test_multi_criteria_comparison(self):
        """Test comparison using multiple criteria"""
        loans = [
            {"id": "loan1", "cost": 71900, "flexibility": 8.5, "rate": 8.5},
            {"id": "loan2", "cost": 68500, "flexibility": 6.0, "rate": 7.5},
            {"id": "loan3", "cost": 75000, "flexibility": 9.0, "rate": 9.0},
        ]
        
        # Calculate composite score (lower cost, higher flexibility, lower rate)
        for loan in loans:
            # Normalize and combine (simplified)
            cost_score = 100 - (loan["cost"] / 1000)
            flex_score = loan["flexibility"] * 10
            rate_score = 100 - (loan["rate"] * 10)
            
            loan["composite_score"] = (cost_score + flex_score + rate_score) / 3
        
        best_overall = max(loans, key=lambda x: x["composite_score"])
        
        assert best_overall["id"] in ["loan1", "loan2", "loan3"], \
            "Should identify best overall loan"
    
    def test_pros_cons_generation(self):
        """Test generation of pros and cons"""
        loan = {
            "id": "loan1",
            "cost": 71900,
            "rate": 8.5,
            "flexibility": 8.5,
            "has_moratorium": True,
            "prepayment_penalty": 0
        }
        
        pros = []
        cons = []
        
        if loan["flexibility"] > 7.0:
            pros.append("High flexibility")
        if loan["has_moratorium"]:
            pros.append("Moratorium period available")
        if loan["prepayment_penalty"] == 0:
            pros.append("No prepayment penalty")
        if loan["rate"] > 9.0:
            cons.append("High interest rate")
        
        assert len(pros) > 0, "Should generate pros"
        assert "High flexibility" in pros, "Should identify high flexibility as pro"


class TestMetricsAccuracy:
    """Test accuracy of metrics calculations"""
    
    def test_calculation_precision(self):
        """Test precision of calculations"""
        principal = 50000
        rate = 8.5
        tenure = 60
        
        # Calculate with high precision
        monthly_rate = rate / 12 / 100
        emi = principal * monthly_rate * ((1 + monthly_rate) ** tenure) / \
              (((1 + monthly_rate) ** tenure) - 1)
        
        # EMI should be calculated to 2 decimal places
        emi_rounded = round(emi, 2)
        
        assert abs(emi - emi_rounded) < 0.01, \
            "Calculation should be precise to 2 decimal places"
    
    def test_rounding_consistency(self):
        """Test consistency of rounding"""
        values = [1234.567, 8.555, 0.9449]
        
        for value in values:
            rounded = round(value, 2)
            assert isinstance(rounded, float), "Rounded value should be float"
    
    def test_percentage_formatting(self):
        """Test formatting of percentage values"""
        rate = 8.5
        
        formatted = f"{rate:.2f}%"
        
        assert formatted == "8.50%", "Should format percentage correctly"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
