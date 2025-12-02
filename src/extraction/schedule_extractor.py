"""
Payment schedule extractor for loan documents.
Handles extraction of payment schedules from tables including dates, amounts, and components.
"""

import re
from typing import Optional, Dict, Any, List
from datetime import datetime


class PaymentScheduleExtractor:
    """Extracts payment schedule information from table data."""
    
    def __init__(self):
        # Common date formats
        self.date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',  # DD-MM-YYYY or DD/MM/YYYY
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',    # YYYY-MM-DD
            r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}',  # DD Mon YYYY
        ]
    
    def parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse date string to standardized format.
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            Standardized date string (YYYY-MM-DD) or None
        """
        date_str = date_str.strip()
        
        # Try different date formats
        date_formats = [
            '%d-%m-%Y', '%d/%m/%Y', '%d-%m-%y', '%d/%m/%y',
            '%Y-%m-%d', '%Y/%m/%d',
            '%d %b %Y', '%d %B %Y', '%d-%b-%Y', '%d-%B-%Y'
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    
    def parse_amount(self, amount_str: str) -> Optional[float]:
        """
        Parse amount string to float.
        
        Args:
            amount_str: Amount string with possible currency symbols and commas
            
        Returns:
            Float value or None
        """
        # Remove currency symbols and commas
        cleaned = re.sub(r'[₹Rs\.,\s]', '', amount_str)
        cleaned = cleaned.replace(',', '')
        
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    def identify_schedule_columns(self, headers: List[str]) -> Dict[str, int]:
        """
        Identify relevant columns in payment schedule table.
        
        Args:
            headers: List of table headers
            
        Returns:
            Dictionary mapping column types to indices
        """
        headers_lower = [h.lower() for h in headers]
        column_map = {}
        
        # Identify payment number/installment column
        for i, header in enumerate(headers_lower):
            if any(term in header for term in ['installment', 'payment no', 'emi no', 'no.', 'sr.', 'serial']):
                column_map['payment_number'] = i
                break
        
        # Identify date column
        for i, header in enumerate(headers_lower):
            if any(term in header for term in ['date', 'due date', 'payment date', 'emi date']):
                column_map['date'] = i
                break
        
        # Identify total amount column
        for i, header in enumerate(headers_lower):
            if any(term in header for term in ['total', 'emi amount', 'payment amount', 'installment amount']):
                if 'principal' not in header and 'interest' not in header:
                    column_map['total_amount'] = i
                    break
        
        # Identify principal component column
        for i, header in enumerate(headers_lower):
            if 'principal' in header:
                column_map['principal'] = i
                break
        
        # Identify interest component column
        for i, header in enumerate(headers_lower):
            if 'interest' in header:
                column_map['interest'] = i
                break
        
        # Identify outstanding balance column
        for i, header in enumerate(headers_lower):
            if any(term in header for term in ['outstanding', 'balance', 'remaining']):
                column_map['outstanding'] = i
                break
        
        return column_map
    
    def extract_payment_schedule(self, table_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Extract payment schedule from table data.
        
        Args:
            table_data: Structured table data with headers and rows
            
        Returns:
            List of payment schedule entries or None
        """
        if not table_data or 'headers' not in table_data or 'rows' not in table_data:
            return None
        
        headers = table_data['headers']
        rows = table_data['rows']
        
        # Identify columns
        column_map = self.identify_schedule_columns(headers)
        
        # Need at least date and amount columns
        if 'date' not in column_map and 'total_amount' not in column_map:
            return None
        
        schedule = []
        
        for row_idx, row in enumerate(rows):
            if len(row) < len(headers):
                continue
            
            entry = {}
            
            # Extract payment number
            if 'payment_number' in column_map:
                try:
                    entry['payment_number'] = int(re.sub(r'\D', '', row[column_map['payment_number']]))
                except (ValueError, IndexError):
                    entry['payment_number'] = row_idx + 1
            else:
                entry['payment_number'] = row_idx + 1
            
            # Extract date
            if 'date' in column_map:
                date_str = row[column_map['date']].strip()
                parsed_date = self.parse_date(date_str)
                if parsed_date:
                    entry['payment_date'] = parsed_date
                else:
                    entry['payment_date'] = date_str
            
            # Extract total amount
            if 'total_amount' in column_map:
                amount = self.parse_amount(row[column_map['total_amount']])
                if amount is not None:
                    entry['total_amount'] = amount
            
            # Extract principal component
            if 'principal' in column_map:
                principal = self.parse_amount(row[column_map['principal']])
                if principal is not None:
                    entry['principal_component'] = principal
            
            # Extract interest component
            if 'interest' in column_map:
                interest = self.parse_amount(row[column_map['interest']])
                if interest is not None:
                    entry['interest_component'] = interest
            
            # Extract outstanding balance
            if 'outstanding' in column_map:
                outstanding = self.parse_amount(row[column_map['outstanding']])
                if outstanding is not None:
                    entry['outstanding_balance'] = outstanding
            
            # Only add entry if it has meaningful data
            if 'total_amount' in entry or 'principal_component' in entry:
                entry['confidence'] = 0.9
                schedule.append(entry)
        
        return schedule if schedule else None
    
    def extract_schedule_from_tables(self, tables: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """
        Extract payment schedule from multiple tables.
        
        Args:
            tables: List of table data structures
            
        Returns:
            Combined payment schedule or None
        """
        all_schedules = []
        
        for table in tables:
            schedule = self.extract_payment_schedule(table)
            if schedule:
                all_schedules.extend(schedule)
        
        # Sort by payment number if available
        if all_schedules:
            all_schedules.sort(key=lambda x: x.get('payment_number', 0))
            return all_schedules
        
        return None
    
    def calculate_schedule_summary(self, schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate summary statistics from payment schedule.
        
        Args:
            schedule: List of payment schedule entries
            
        Returns:
            Dictionary with summary statistics
        """
        if not schedule:
            return {}
        
        summary = {
            'total_payments': len(schedule),
            'total_amount_payable': 0,
            'total_principal': 0,
            'total_interest': 0
        }
        
        for entry in schedule:
            if 'total_amount' in entry:
                summary['total_amount_payable'] += entry['total_amount']
            if 'principal_component' in entry:
                summary['total_principal'] += entry['principal_component']
            if 'interest_component' in entry:
                summary['total_interest'] += entry['interest_component']
        
        # Calculate average EMI
        if summary['total_payments'] > 0:
            summary['average_emi'] = summary['total_amount_payable'] / summary['total_payments']
        
        return summary
