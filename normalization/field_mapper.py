"""
Field mapper for normalizing extracted loan data to standardized schema.

This module handles mapping of bank-specific field names and formats to the
standardized NormalizedLoanData schema, including data type normalization.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date
import re
from decimal import Decimal

from .data_models import (
    NormalizedLoanData, BankInfo, CoSignerDetails, FeeItem,
    PaymentScheduleEntry, LoanType
)


class FieldMapper:
    """Maps extracted fields to standardized schema with data normalization."""
    
    # Field name mappings for common variations
    FIELD_MAPPINGS = {
        'principal': ['principal', 'loan_amount', 'principal_amount', 'amount', 'loan_amt', 'sanctioned_amount'],
        'interest_rate': ['interest_rate', 'rate', 'interest', 'roi', 'rate_of_interest', 'annual_rate', 'apr'],
        'tenure': ['tenure', 'loan_tenure', 'period', 'loan_period', 'duration', 'term', 'loan_term'],
        'moratorium': ['moratorium', 'grace_period', 'moratorium_period', 'grace', 'holiday_period'],
        'bank_name': ['bank_name', 'lender', 'bank', 'lender_name', 'institution', 'financial_institution'],
        'branch': ['branch', 'branch_name', 'branch_office', 'office'],
        'processing_fee': ['processing_fee', 'processing_charges', 'processing', 'upfront_fee'],
        'late_penalty': ['late_payment_penalty', 'late_fee', 'penalty', 'late_charges', 'overdue_charges'],
        'prepayment_penalty': ['prepayment_penalty', 'foreclosure_charges', 'prepayment_charges', 'early_payment_fee'],
        'repayment_mode': ['repayment_mode', 'payment_mode', 'repayment_type', 'payment_type'],
        'co_signer_name': ['co_signer', 'cosigner', 'guarantor', 'co_applicant', 'joint_applicant'],
        'collateral': ['collateral', 'security', 'pledge', 'mortgage'],
        'disbursement': ['disbursement', 'disbursement_terms', 'payout', 'release_terms'],
    }
    
    # Currency symbols and codes
    CURRENCY_PATTERNS = {
        '₹': 'INR',
        'Rs': 'INR',
        'Rs.': 'INR',
        'INR': 'INR',
        '$': 'USD',
        'USD': 'USD',
        '€': 'EUR',
        'EUR': 'EUR',
        '£': 'GBP',
        'GBP': 'GBP',
    }
    
    def __init__(self):
        """Initialize the field mapper."""
        self.warnings: List[str] = []
    
    def map_fields(self, extracted_data: Dict[str, Any], document_id: str, loan_id: str) -> Dict[str, Any]:
        """
        Map extracted fields to standardized schema.
        
        Args:
            extracted_data: Raw extracted data from extraction module
            document_id: ID of source document
            loan_id: ID for the loan record
            
        Returns:
            Dictionary with normalized field names and values
        """
        self.warnings = []
        
        normalized = {
            'loan_id': loan_id,
            'document_id': document_id,
            'extraction_timestamp': datetime.now(),
            'raw_extracted_data': extracted_data,
        }
        
        # Map loan type
        normalized['loan_type'] = self._map_loan_type(extracted_data)
        
        # Map bank information
        normalized['bank_info'] = self._map_bank_info(extracted_data)
        
        # Map core loan terms
        normalized['principal_amount'] = self._map_principal(extracted_data)
        normalized['currency'] = self._map_currency(extracted_data)
        normalized['interest_rate'] = self._map_interest_rate(extracted_data)
        normalized['tenure_months'] = self._map_tenure(extracted_data)
        normalized['moratorium_period_months'] = self._map_moratorium(extracted_data)
        
        # Map fees
        normalized['fees'] = self._map_fees(extracted_data)
        normalized['processing_fee'] = self._map_processing_fee(extracted_data)
        normalized['late_payment_penalty'] = self._map_late_penalty(extracted_data)
        normalized['prepayment_penalty'] = self._map_prepayment_penalty(extracted_data)
        
        # Map repayment details
        normalized['repayment_mode'] = self._map_repayment_mode(extracted_data)
        normalized['payment_schedule'] = self._map_payment_schedule(extracted_data)
        
        # Map additional details
        normalized['co_signer'] = self._map_co_signer(extracted_data)
        normalized['collateral_details'] = self._map_collateral(extracted_data)
        normalized['disbursement_terms'] = self._map_disbursement(extracted_data)
        
        # Map confidence score
        normalized['extraction_confidence'] = self._map_confidence(extracted_data)
        
        return normalized
    
    def _find_field(self, data: Dict[str, Any], field_key: str) -> Optional[Any]:
        """Find a field value using multiple possible key names."""
        if field_key not in self.FIELD_MAPPINGS:
            return data.get(field_key)
        
        for possible_key in self.FIELD_MAPPINGS[field_key]:
            # Try exact match
            if possible_key in data:
                return data[possible_key]
            
            # Try case-insensitive match
            for key in data.keys():
                if key.lower() == possible_key.lower():
                    return data[key]
        
        return None
    
    def _map_loan_type(self, data: Dict[str, Any]) -> LoanType:
        """Map loan type from extracted data."""
        loan_type_str = data.get('loan_type', '').lower()
        
        if not loan_type_str:
            self.warnings.append("Loan type not found, defaulting to 'other'")
            return LoanType.OTHER
        
        # Map common variations
        if 'education' in loan_type_str or 'student' in loan_type_str:
            return LoanType.EDUCATION
        elif 'home' in loan_type_str or 'housing' in loan_type_str or 'mortgage' in loan_type_str:
            return LoanType.HOME
        elif 'personal' in loan_type_str:
            return LoanType.PERSONAL
        elif 'vehicle' in loan_type_str or 'car' in loan_type_str or 'auto' in loan_type_str:
            return LoanType.VEHICLE
        elif 'gold' in loan_type_str:
            return LoanType.GOLD
        else:
            return LoanType.OTHER
    
    def _map_bank_info(self, data: Dict[str, Any]) -> BankInfo:
        """Map bank information from extracted data."""
        bank_name = self._find_field(data, 'bank_name')
        branch_name = self._find_field(data, 'branch')
        bank_code = data.get('bank_code') or data.get('ifsc') or data.get('swift_code')
        
        if not bank_name:
            bank_name = "Unknown Bank"
            self.warnings.append("Bank name not found")
        
        return BankInfo(
            bank_name=str(bank_name),
            branch_name=str(branch_name) if branch_name else None,
            bank_code=str(bank_code) if bank_code else None
        )
    
    def _map_principal(self, data: Dict[str, Any]) -> float:
        """Map and normalize principal amount."""
        principal = self._find_field(data, 'principal')
        
        if principal is None:
            raise ValueError("Principal amount is required but not found")
        
        return self._normalize_currency_value(principal)
    
    def _map_currency(self, data: Dict[str, Any]) -> str:
        """Map currency from extracted data."""
        currency = data.get('currency', 'INR')
        
        # Check if currency is a symbol
        if currency in self.CURRENCY_PATTERNS:
            return self.CURRENCY_PATTERNS[currency]
        
        # Default to INR if not recognized
        if len(currency) != 3:
            self.warnings.append(f"Unrecognized currency '{currency}', defaulting to INR")
            return 'INR'
        
        return currency.upper()
    
    def _map_interest_rate(self, data: Dict[str, Any]) -> float:
        """Map and normalize interest rate."""
        rate = self._find_field(data, 'interest_rate')
        
        if rate is None:
            raise ValueError("Interest rate is required but not found")
        
        return self._normalize_percentage(rate)
    
    def _map_tenure(self, data: Dict[str, Any]) -> int:
        """Map and normalize tenure to months."""
        tenure = self._find_field(data, 'tenure')
        
        if tenure is None:
            raise ValueError("Tenure is required but not found")
        
        # Check if tenure is specified in years
        tenure_str = str(tenure).lower()
        if 'year' in tenure_str:
            # Extract number and convert to months
            years = self._extract_number(tenure_str)
            return int(years * 12)
        elif 'month' in tenure_str:
            return int(self._extract_number(tenure_str))
        else:
            # Assume it's already in months
            return int(self._extract_number(tenure_str))
    
    def _map_moratorium(self, data: Dict[str, Any]) -> Optional[int]:
        """Map and normalize moratorium period to months."""
        moratorium = self._find_field(data, 'moratorium')
        
        if moratorium is None:
            return None
        
        # Handle "None" or "N/A" strings
        moratorium_str = str(moratorium).lower()
        if moratorium_str in ['none', 'n/a', 'na', 'nil', '0']:
            return 0
        
        # Check if specified in years
        if 'year' in moratorium_str:
            years = self._extract_number(moratorium_str)
            return int(years * 12)
        elif 'month' in moratorium_str:
            return int(self._extract_number(moratorium_str))
        else:
            return int(self._extract_number(moratorium_str))
    
    def _map_fees(self, data: Dict[str, Any]) -> List[FeeItem]:
        """Map fee items from extracted data."""
        fees = []
        
        # Check for fees list
        if 'fees' in data and isinstance(data['fees'], list):
            for fee_data in data['fees']:
                if isinstance(fee_data, dict):
                    fee_item = self._create_fee_item(fee_data)
                    if fee_item:
                        fees.append(fee_item)
        
        # Check for individual fee fields
        fee_fields = ['processing_fee', 'administrative_fee', 'documentation_fee', 
                     'legal_fee', 'valuation_fee', 'stamp_duty']
        
        for field in fee_fields:
            value = data.get(field)
            if value and value not in [0, '0', 'nil', 'N/A']:
                fee_type = field.replace('_', ' ').title()
                amount = self._normalize_currency_value(value)
                fees.append(FeeItem(
                    fee_type=fee_type,
                    amount=amount,
                    currency=self._map_currency(data)
                ))
        
        return fees
    
    def _create_fee_item(self, fee_data: Dict[str, Any]) -> Optional[FeeItem]:
        """Create a FeeItem from fee data dictionary."""
        try:
            fee_type = fee_data.get('type') or fee_data.get('fee_type') or 'Unknown Fee'
            amount = self._normalize_currency_value(fee_data.get('amount', 0))
            currency = fee_data.get('currency', 'INR')
            conditions = fee_data.get('conditions') or fee_data.get('notes')
            
            return FeeItem(
                fee_type=str(fee_type),
                amount=amount,
                currency=currency,
                conditions=str(conditions) if conditions else None
            )
        except Exception as e:
            self.warnings.append(f"Failed to parse fee item: {e}")
            return None
    
    def _map_processing_fee(self, data: Dict[str, Any]) -> Optional[float]:
        """Map processing fee specifically."""
        fee = self._find_field(data, 'processing_fee')
        
        if fee is None or str(fee).lower() in ['nil', 'n/a', 'na', '0']:
            return None
        
        return self._normalize_currency_value(fee)
    
    def _map_late_penalty(self, data: Dict[str, Any]) -> Optional[str]:
        """Map late payment penalty terms."""
        penalty = self._find_field(data, 'late_penalty')
        return str(penalty) if penalty else None
    
    def _map_prepayment_penalty(self, data: Dict[str, Any]) -> Optional[str]:
        """Map prepayment penalty terms."""
        penalty = self._find_field(data, 'prepayment_penalty')
        return str(penalty) if penalty else None
    
    def _map_repayment_mode(self, data: Dict[str, Any]) -> Optional[str]:
        """Map repayment mode."""
        mode = self._find_field(data, 'repayment_mode')
        
        if mode:
            mode_str = str(mode).lower()
            if 'emi' in mode_str or 'equated' in mode_str:
                return 'emi'
            elif 'bullet' in mode_str or 'lump' in mode_str:
                return 'bullet'
            elif 'step' in mode_str:
                return 'step-up'
        
        return mode
    
    def _map_payment_schedule(self, data: Dict[str, Any]) -> Optional[List[PaymentScheduleEntry]]:
        """Map payment schedule from extracted data."""
        schedule_data = data.get('payment_schedule')
        
        if not schedule_data or not isinstance(schedule_data, list):
            return None
        
        schedule = []
        for entry_data in schedule_data:
            try:
                entry = self._create_payment_entry(entry_data)
                if entry:
                    schedule.append(entry)
            except Exception as e:
                self.warnings.append(f"Failed to parse payment schedule entry: {e}")
        
        return schedule if schedule else None
    
    def _create_payment_entry(self, entry_data: Dict[str, Any]) -> Optional[PaymentScheduleEntry]:
        """Create a PaymentScheduleEntry from entry data."""
        payment_number = int(entry_data.get('payment_number', 0))
        payment_date = self._parse_date(entry_data.get('payment_date'))
        total_amount = self._normalize_currency_value(entry_data.get('total_amount', 0))
        principal = self._normalize_currency_value(entry_data.get('principal', 0))
        interest = self._normalize_currency_value(entry_data.get('interest', 0))
        balance = self._normalize_currency_value(entry_data.get('balance', 0))
        
        if not payment_date:
            return None
        
        return PaymentScheduleEntry(
            payment_number=payment_number,
            payment_date=payment_date,
            total_amount=total_amount,
            principal_component=principal,
            interest_component=interest,
            outstanding_balance=balance
        )
    
    def _map_co_signer(self, data: Dict[str, Any]) -> Optional[CoSignerDetails]:
        """Map co-signer details."""
        co_signer_name = self._find_field(data, 'co_signer_name')
        
        if not co_signer_name:
            return None
        
        relationship = data.get('co_signer_relationship', 'Unknown')
        contact = data.get('co_signer_contact')
        
        return CoSignerDetails(
            name=str(co_signer_name),
            relationship=str(relationship),
            contact=str(contact) if contact else None
        )
    
    def _map_collateral(self, data: Dict[str, Any]) -> Optional[str]:
        """Map collateral details."""
        collateral = self._find_field(data, 'collateral')
        return str(collateral) if collateral else None
    
    def _map_disbursement(self, data: Dict[str, Any]) -> Optional[str]:
        """Map disbursement terms."""
        disbursement = self._find_field(data, 'disbursement')
        return str(disbursement) if disbursement else None
    
    def _map_confidence(self, data: Dict[str, Any]) -> float:
        """Map extraction confidence score."""
        confidence = data.get('confidence', data.get('extraction_confidence', 0.0))
        
        try:
            conf_float = float(confidence)
            # Ensure it's between 0 and 1
            return max(0.0, min(1.0, conf_float))
        except (ValueError, TypeError):
            self.warnings.append("Invalid confidence score, defaulting to 0.0")
            return 0.0
    
    def _normalize_currency_value(self, value: Any) -> float:
        """Normalize currency value to float."""
        if isinstance(value, (int, float)):
            return float(value)
        
        # Remove currency symbols and commas
        value_str = str(value)
        for symbol in self.CURRENCY_PATTERNS.keys():
            value_str = value_str.replace(symbol, '')
        
        value_str = value_str.replace(',', '').replace(' ', '').strip()
        
        # Extract number
        return self._extract_number(value_str)
    
    def _normalize_percentage(self, value: Any) -> float:
        """Normalize percentage value to float."""
        if isinstance(value, (int, float)):
            return float(value)
        
        value_str = str(value).replace('%', '').replace(' ', '').strip()
        return self._extract_number(value_str)
    
    def _extract_number(self, text: str) -> float:
        """Extract numeric value from text."""
        # Remove all non-numeric characters except decimal point and minus
        cleaned = re.sub(r'[^\d.-]', '', str(text))
        
        if not cleaned or cleaned == '-':
            return 0.0
        
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def _parse_date(self, date_value: Any) -> Optional[date]:
        """Parse date from various formats."""
        if isinstance(date_value, date):
            return date_value
        
        if isinstance(date_value, datetime):
            return date_value.date()
        
        if not date_value:
            return None
        
        date_str = str(date_value).strip()
        
        # Try common date formats
        formats = [
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y/%m/%d',
            '%d-%b-%Y',
            '%d %b %Y',
            '%d-%B-%Y',
            '%d %B %Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        self.warnings.append(f"Could not parse date: {date_value}")
        return None
    
    def get_warnings(self) -> List[str]:
        """Get list of warnings from the mapping process."""
        return self.warnings
