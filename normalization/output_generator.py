"""
JSON output generator for structured loan data.

This module generates JSON output documents with all extracted fields,
table structures, and proper data type formatting.
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .data_models import (
    NormalizedLoanData,
    TableData,
    PaymentScheduleEntry,
    FeeItem,
    ComparisonMetrics
)


class JSONOutputGenerator:
    """Generates structured JSON output from normalized loan data."""
    
    def __init__(self, output_directory: Optional[str] = None):
        """
        Initialize the JSON output generator.
        
        Args:
            output_directory: Directory to save JSON output files. 
                            If None, returns JSON string only.
        """
        self.output_directory = Path(output_directory) if output_directory else None
        if self.output_directory:
            self.output_directory.mkdir(parents=True, exist_ok=True)
    
    def generate_output_document(
        self, 
        loan_data: NormalizedLoanData,
        comparison_metrics: Optional[ComparisonMetrics] = None,
        save_to_file: bool = True
    ) -> Dict[str, Any]:
        """
        Generate complete output document in JSON format.
        
        Args:
            loan_data: Normalized loan data
            comparison_metrics: Optional comparison metrics
            save_to_file: Whether to save to file
            
        Returns:
            Dictionary containing structured output document
        """
        output_doc = {
            "document_info": {
                "loan_id": loan_data.loan_id,
                "document_id": loan_data.document_id,
                "extraction_timestamp": loan_data.extraction_timestamp.isoformat(),
                "extraction_confidence": loan_data.extraction_confidence
            },
            "loan_classification": {
                "loan_type": loan_data.loan_type.value,
                "bank_info": self._format_bank_info(loan_data.bank_info) if loan_data.bank_info else None
            },
            "core_terms": {
                "principal_amount": loan_data.principal_amount,
                "currency": loan_data.currency,
                "interest_rate": loan_data.interest_rate,
                "tenure_months": loan_data.tenure_months,
                "moratorium_period_months": loan_data.moratorium_period_months,
                "repayment_mode": loan_data.repayment_mode
            },
            "fees_and_charges": {
                "processing_fee": loan_data.processing_fee,
                "late_payment_penalty": loan_data.late_payment_penalty,
                "prepayment_penalty": loan_data.prepayment_penalty,
                "detailed_fees": [self._format_fee_item(fee) for fee in loan_data.fees]
            },
            "payment_schedule": [
                self._format_payment_entry(entry) 
                for entry in loan_data.payment_schedule
            ],
            "additional_details": {
                "co_signer": self._format_co_signer(loan_data.co_signer) if loan_data.co_signer else None,
                "collateral_details": loan_data.collateral_details,
                "disbursement_terms": loan_data.disbursement_terms
            },
            "extracted_tables": [
                self._format_table_structure(table) 
                for table in loan_data.tables
            ],
            "raw_fields": loan_data.raw_extracted_fields
        }
        
        # Add comparison metrics if provided
        if comparison_metrics:
            output_doc["comparison_metrics"] = self._format_comparison_metrics(comparison_metrics)
        
        # Save to file if requested
        if save_to_file and self.output_directory:
            self._save_to_file(output_doc, loan_data.loan_id)
        
        return output_doc
    
    def _format_bank_info(self, bank_info) -> Dict[str, Any]:
        """Format bank information."""
        return {
            "bank_name": bank_info.bank_name,
            "branch_name": bank_info.branch_name,
            "bank_code": bank_info.bank_code
        }
    
    def _format_fee_item(self, fee: FeeItem) -> Dict[str, Any]:
        """Format individual fee item."""
        return {
            "fee_type": fee.fee_type,
            "amount": fee.amount,
            "currency": fee.currency,
            "conditions": fee.conditions
        }
    
    def _format_payment_entry(self, entry: PaymentScheduleEntry) -> Dict[str, Any]:
        """Format payment schedule entry."""
        return {
            "payment_number": entry.payment_number,
            "payment_date": entry.payment_date,
            "total_amount": entry.total_amount,
            "principal_component": entry.principal_component,
            "interest_component": entry.interest_component,
            "outstanding_balance": entry.outstanding_balance
        }
    
    def _format_co_signer(self, co_signer) -> Dict[str, Any]:
        """Format co-signer details."""
        return {
            "name": co_signer.name,
            "relationship": co_signer.relationship,
            "contact": co_signer.contact
        }
    
    def _format_table_structure(self, table: TableData) -> Dict[str, Any]:
        """
        Format table structure with preserved relationships.
        
        Includes nested column hierarchies and proper data type formatting.
        """
        formatted_table = {
            "table_id": table.table_id,
            "table_type": table.table_type,
            "headers": table.headers,
            "data": []
        }
        
        # Format rows with proper data types
        for row in table.rows:
            formatted_row = []
            for cell in row:
                formatted_cell = self._format_mixed_content(cell)
                formatted_row.append(formatted_cell)
            formatted_table["data"].append(formatted_row)
        
        # Include nested column hierarchies if present
        if table.nested_columns:
            formatted_table["nested_columns"] = table.nested_columns
        
        # Create structured representation with header-data mapping
        formatted_table["structured_data"] = self._create_structured_table_data(
            table.headers, 
            table.rows
        )
        
        return formatted_table
    
    def _format_mixed_content(self, content: str) -> Any:
        """
        Format mixed content with proper data types.
        
        Attempts to convert strings to appropriate types (int, float)
        while preserving text and special characters.
        """
        if not isinstance(content, str):
            return content
        
        # Try to convert to number
        content_stripped = content.strip()
        
        # Remove common currency symbols and percentage signs for parsing
        numeric_content = content_stripped.replace(',', '').replace('₹', '').replace('$', '').replace('%', '')
        
        try:
            # Try integer first
            if '.' not in numeric_content:
                return int(numeric_content)
            # Try float
            return float(numeric_content)
        except ValueError:
            # Return as string if not a number
            return content_stripped
    
    def _create_structured_table_data(
        self, 
        headers: list, 
        rows: list
    ) -> list:
        """
        Create structured table data with header-row associations.
        
        Returns list of dictionaries mapping headers to row values.
        """
        structured_data = []
        for row in rows:
            row_dict = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    row_dict[header] = self._format_mixed_content(row[i])
            structured_data.append(row_dict)
        return structured_data
    
    def _format_comparison_metrics(self, metrics: ComparisonMetrics) -> Dict[str, Any]:
        """Format comparison metrics."""
        return {
            "total_cost_estimate": metrics.total_cost_estimate,
            "effective_interest_rate": metrics.effective_interest_rate,
            "flexibility_score": metrics.flexibility_score,
            "monthly_emi": metrics.monthly_emi,
            "total_interest_payable": metrics.total_interest_payable,
            "calculation_timestamp": metrics.calculation_timestamp.isoformat()
        }
    
    def _save_to_file(self, output_doc: Dict[str, Any], loan_id: str) -> None:
        """
        Save output document to JSON file.
        
        Args:
            output_doc: Output document dictionary
            loan_id: Loan ID for filename
        """
        filename = f"loan_{loan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_directory / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_doc, f, indent=2, ensure_ascii=False)
    
    def generate_json_string(
        self, 
        loan_data: NormalizedLoanData,
        comparison_metrics: Optional[ComparisonMetrics] = None,
        pretty: bool = True
    ) -> str:
        """
        Generate JSON string representation.
        
        Args:
            loan_data: Normalized loan data
            comparison_metrics: Optional comparison metrics
            pretty: Whether to format with indentation
            
        Returns:
            JSON string
        """
        output_doc = self.generate_output_document(
            loan_data, 
            comparison_metrics, 
            save_to_file=False
        )
        
        if pretty:
            return json.dumps(output_doc, indent=2, ensure_ascii=False)
        return json.dumps(output_doc, ensure_ascii=False)
    
    def link_to_source_document(
        self, 
        output_doc: Dict[str, Any], 
        source_document_path: str
    ) -> Dict[str, Any]:
        """
        Link output document to source document.
        
        Args:
            output_doc: Output document dictionary
            source_document_path: Path to source document
            
        Returns:
            Updated output document with source link
        """
        output_doc["source_document"] = {
            "path": source_document_path,
            "linked_at": datetime.now().isoformat()
        }
        return output_doc
