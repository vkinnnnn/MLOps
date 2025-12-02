"""
Confidence scoring module for extracted loan data.
Calculates extraction confidence for each field and flags low-confidence extractions.
"""

from typing import Dict, Any, List, Optional


class ConfidenceScorer:
    """Calculates and manages confidence scores for extracted loan data."""
    
    def __init__(self, low_confidence_threshold: float = 0.7):
        """
        Initialize confidence scorer.
        
        Args:
            low_confidence_threshold: Threshold below which extractions are flagged
        """
        self.low_confidence_threshold = low_confidence_threshold
        
        # Field importance weights for overall confidence calculation
        self.field_weights = {
            'principal_amount': 0.20,
            'interest_rate': 0.20,
            'tenure': 0.15,
            'bank_name': 0.10,
            'processing_fee': 0.05,
            'late_payment_penalty': 0.05,
            'prepayment_penalty': 0.05,
            'repayment_mode': 0.05,
            'moratorium_period': 0.05,
            'disbursement_terms': 0.05,
            'cosigner': 0.03,
            'collateral': 0.02
        }
    
    def calculate_field_confidence(self, field_data: Optional[Dict[str, Any]]) -> float:
        """
        Calculate confidence score for a single field.
        
        Args:
            field_data: Extracted field data with confidence score
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if field_data is None:
            return 0.0
        
        # If field already has confidence score, use it
        if 'confidence' in field_data:
            return field_data['confidence']
        
        # Default confidence if no score provided
        return 0.5
    
    def calculate_overall_confidence(self, extracted_data: Dict[str, Any]) -> float:
        """
        Calculate overall confidence score for all extracted data.
        
        Args:
            extracted_data: Dictionary containing all extracted fields
            
        Returns:
            Overall confidence score between 0.0 and 1.0
        """
        total_weight = 0.0
        weighted_confidence = 0.0
        
        # Calculate weighted confidence for core fields
        if 'core_fields' in extracted_data:
            core = extracted_data['core_fields']
            
            if 'principal_amount' in core:
                conf = self.calculate_field_confidence(core['principal_amount'])
                weighted_confidence += conf * self.field_weights.get('principal_amount', 0)
                total_weight += self.field_weights.get('principal_amount', 0)
            
            if 'interest_rate' in core:
                conf = self.calculate_field_confidence(core['interest_rate'])
                weighted_confidence += conf * self.field_weights.get('interest_rate', 0)
                total_weight += self.field_weights.get('interest_rate', 0)
            
            if 'tenure' in core:
                conf = self.calculate_field_confidence(core['tenure'])
                weighted_confidence += conf * self.field_weights.get('tenure', 0)
                total_weight += self.field_weights.get('tenure', 0)
            
            if 'moratorium_period' in core:
                conf = self.calculate_field_confidence(core['moratorium_period'])
                weighted_confidence += conf * self.field_weights.get('moratorium_period', 0)
                total_weight += self.field_weights.get('moratorium_period', 0)
        
        # Calculate weighted confidence for fees
        if 'fees' in extracted_data and extracted_data['fees']:
            fees_confidence = 0.0
            fees_count = 0
            
            for fee in extracted_data['fees']:
                fees_confidence += self.calculate_field_confidence(fee)
                fees_count += 1
            
            if fees_count > 0:
                avg_fees_confidence = fees_confidence / fees_count
                weighted_confidence += avg_fees_confidence * self.field_weights.get('processing_fee', 0)
                total_weight += self.field_weights.get('processing_fee', 0)
        
        # Calculate weighted confidence for penalties
        if 'penalties' in extracted_data and extracted_data['penalties']:
            penalties_confidence = 0.0
            penalties_count = 0
            
            for penalty in extracted_data['penalties']:
                penalties_confidence += self.calculate_field_confidence(penalty)
                penalties_count += 1
            
            if penalties_count > 0:
                avg_penalties_confidence = penalties_confidence / penalties_count
                weighted_confidence += avg_penalties_confidence * (
                    self.field_weights.get('late_payment_penalty', 0) + 
                    self.field_weights.get('prepayment_penalty', 0)
                )
                total_weight += (
                    self.field_weights.get('late_payment_penalty', 0) + 
                    self.field_weights.get('prepayment_penalty', 0)
                )
        
        # Calculate weighted confidence for entities
        if 'entities' in extracted_data:
            entities = extracted_data['entities']
            
            if 'lender' in entities and entities['lender']:
                bank_conf = entities['lender'].get('bank_confidence', 0.5)
                weighted_confidence += bank_conf * self.field_weights.get('bank_name', 0)
                total_weight += self.field_weights.get('bank_name', 0)
            
            if 'cosigner' in entities:
                cosigner_conf = self.calculate_field_confidence(entities['cosigner'])
                weighted_confidence += cosigner_conf * self.field_weights.get('cosigner', 0)
                total_weight += self.field_weights.get('cosigner', 0)
            
            if 'collateral' in entities:
                collateral_conf = self.calculate_field_confidence(entities['collateral'])
                weighted_confidence += collateral_conf * self.field_weights.get('collateral', 0)
                total_weight += self.field_weights.get('collateral', 0)
        
        # Calculate weighted confidence for additional terms
        if 'additional_terms' in extracted_data:
            terms = extracted_data['additional_terms']
            
            if 'repayment_mode' in terms:
                mode_conf = self.calculate_field_confidence(terms['repayment_mode'])
                weighted_confidence += mode_conf * self.field_weights.get('repayment_mode', 0)
                total_weight += self.field_weights.get('repayment_mode', 0)
            
            if 'disbursement_terms' in terms:
                disb_conf = self.calculate_field_confidence(terms['disbursement_terms'])
                weighted_confidence += disb_conf * self.field_weights.get('disbursement_terms', 0)
                total_weight += self.field_weights.get('disbursement_terms', 0)
        
        # Calculate final confidence
        if total_weight > 0:
            overall_confidence = weighted_confidence / total_weight
        else:
            overall_confidence = 0.0
        
        return round(overall_confidence, 3)
    
    def flag_low_confidence_fields(self, extracted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify and flag fields with low confidence scores.
        
        Args:
            extracted_data: Dictionary containing all extracted fields
            
        Returns:
            List of low-confidence fields with details
        """
        low_confidence_fields = []
        
        def check_field(field_name: str, field_data: Optional[Dict[str, Any]], category: str):
            """Helper function to check a field's confidence."""
            if field_data is not None:
                confidence = self.calculate_field_confidence(field_data)
                if confidence < self.low_confidence_threshold:
                    low_confidence_fields.append({
                        'field_name': field_name,
                        'category': category,
                        'confidence': confidence,
                        'value': field_data.get('value') or field_data.get('description'),
                        'reason': 'Low confidence extraction - manual review recommended'
                    })
        
        # Check core fields
        if 'core_fields' in extracted_data:
            core = extracted_data['core_fields']
            check_field('principal_amount', core.get('principal_amount'), 'core')
            check_field('interest_rate', core.get('interest_rate'), 'core')
            check_field('tenure', core.get('tenure'), 'core')
            check_field('moratorium_period', core.get('moratorium_period'), 'core')
        
        # Check fees
        if 'fees' in extracted_data:
            for i, fee in enumerate(extracted_data['fees']):
                check_field(f"fee_{i}_{fee.get('type', 'unknown')}", fee, 'fees')
        
        # Check penalties
        if 'penalties' in extracted_data:
            for i, penalty in enumerate(extracted_data['penalties']):
                check_field(f"penalty_{i}_{penalty.get('type', 'unknown')}", penalty, 'penalties')
        
        # Check entities
        if 'entities' in extracted_data:
            entities = extracted_data['entities']
            if 'lender' in entities and entities['lender']:
                lender = entities['lender']
                if lender.get('bank_confidence', 1.0) < self.low_confidence_threshold:
                    low_confidence_fields.append({
                        'field_name': 'bank_name',
                        'category': 'entities',
                        'confidence': lender.get('bank_confidence', 0),
                        'value': lender.get('bank_name'),
                        'reason': 'Low confidence extraction - manual review recommended'
                    })
            
            check_field('cosigner', entities.get('cosigner'), 'entities')
            check_field('collateral', entities.get('collateral'), 'entities')
        
        # Check additional terms
        if 'additional_terms' in extracted_data:
            terms = extracted_data['additional_terms']
            check_field('repayment_mode', terms.get('repayment_mode'), 'terms')
            check_field('disbursement_terms', terms.get('disbursement_terms'), 'terms')
        
        return low_confidence_fields
    
    def generate_confidence_report(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive confidence report for extracted data.
        
        Args:
            extracted_data: Dictionary containing all extracted fields
            
        Returns:
            Confidence report with overall score and flagged fields
        """
        overall_confidence = self.calculate_overall_confidence(extracted_data)
        low_confidence_fields = self.flag_low_confidence_fields(extracted_data)
        
        report = {
            'overall_confidence': overall_confidence,
            'confidence_level': self._get_confidence_level(overall_confidence),
            'low_confidence_fields': low_confidence_fields,
            'requires_review': len(low_confidence_fields) > 0 or overall_confidence < self.low_confidence_threshold,
            'field_count': self._count_extracted_fields(extracted_data),
            'missing_critical_fields': self._identify_missing_critical_fields(extracted_data)
        }
        
        return report
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Get human-readable confidence level."""
        if confidence >= 0.9:
            return 'high'
        elif confidence >= 0.7:
            return 'medium'
        else:
            return 'low'
    
    def _count_extracted_fields(self, extracted_data: Dict[str, Any]) -> int:
        """Count total number of extracted fields."""
        count = 0
        
        if 'core_fields' in extracted_data:
            count += sum(1 for v in extracted_data['core_fields'].values() if v is not None)
        
        if 'fees' in extracted_data:
            count += len(extracted_data['fees'])
        
        if 'penalties' in extracted_data:
            count += len(extracted_data['penalties'])
        
        if 'entities' in extracted_data:
            entities = extracted_data['entities']
            if entities.get('lender'):
                count += 1
            if entities.get('cosigner'):
                count += 1
            if entities.get('collateral'):
                count += 1
        
        if 'additional_terms' in extracted_data:
            count += sum(1 for v in extracted_data['additional_terms'].values() if v is not None)
        
        return count
    
    def _identify_missing_critical_fields(self, extracted_data: Dict[str, Any]) -> List[str]:
        """Identify missing critical fields."""
        critical_fields = ['principal_amount', 'interest_rate', 'tenure']
        missing = []
        
        if 'core_fields' in extracted_data:
            core = extracted_data['core_fields']
            for field in critical_fields:
                if field not in core or core[field] is None:
                    missing.append(field)
        else:
            missing = critical_fields
        
        return missing
