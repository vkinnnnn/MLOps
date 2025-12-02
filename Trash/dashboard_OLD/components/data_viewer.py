"""
Data viewer component for displaying extracted loan data.
Displays loan fields, table structures, and confidence scores.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any
from components.responsive_utils import (
    get_responsive_columns,
    mobile_friendly_table,
    responsive_metrics,
    mobile_friendly_tabs
)


def render_data_viewer(api_client):
    """
    Render the extracted data viewer interface.
    
    Args:
        api_client: API client for backend communication
    """
    # Get list of available loans
    try:
        loans = api_client.query_loans()
        
        if not loans:
            st.info("No loan documents have been processed yet. Upload documents to get started.")
            return
        
        # Create selection dropdown
        loan_options = {
            f"{loan.get('bank_info', {}).get('bank_name', 'Unknown Bank')} - {loan.get('loan_type', 'Unknown')} (ID: {loan.get('loan_id', 'N/A')[:8]}...)": loan.get('loan_id')
            for loan in loans
        }
        
        selected_label = st.selectbox(
            "Select a loan document to view:",
            options=list(loan_options.keys())
        )
        
        if selected_label:
            loan_id = loan_options[selected_label]
            selected_loan = next((loan for loan in loans if loan.get('loan_id') == loan_id), None)
            
            if selected_loan:
                display_loan_data(selected_loan)
    
    except Exception as e:
        st.error(f"Error loading loan data: {str(e)}")


def display_loan_data(loan_data: Dict):
    """
    Display detailed loan data in organized sections.
    
    Args:
        loan_data: Dictionary containing normalized loan data
    """
    # Display confidence score at the top
    confidence = loan_data.get('extraction_confidence', 0.0)
    display_confidence_badge(confidence)
    
    st.markdown("---")
    
    # Create tabs for different sections
    tabs = st.tabs([
        "📋 Overview",
        "💰 Financial Details",
        "📊 Tables & Schedules",
        "📄 Additional Information"
    ])
    
    with tabs[0]:
        display_overview_section(loan_data)
    
    with tabs[1]:
        display_financial_details(loan_data)
    
    with tabs[2]:
        display_tables_section(loan_data)
    
    with tabs[3]:
        display_additional_info(loan_data)


def display_confidence_badge(confidence: float):
    """
    Display extraction confidence score with color coding.
    
    Args:
        confidence: Confidence score between 0.0 and 1.0
    """
    confidence_pct = confidence * 100
    
    # Determine color based on confidence level
    if confidence_pct >= 90:
        color = "green"
        status = "High Confidence"
    elif confidence_pct >= 70:
        color = "orange"
        status = "Medium Confidence"
    else:
        color = "red"
        status = "Low Confidence"
    
    # Responsive layout - full width on mobile, centered on desktop
    cols = get_responsive_columns(mobile=1, tablet=1, desktop=3)
    target_col = cols[1] if len(cols) == 3 else cols[0]
    
    with target_col:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 15px; background-color: {color}20; border-radius: 10px; border: 2px solid {color};">
                <h3 style="margin: 0; color: {color}; font-size: clamp(1rem, 4vw, 1.5rem);">Extraction Confidence: {confidence_pct:.1f}%</h3>
                <p style="margin: 5px 0 0 0; color: {color}; font-size: clamp(0.85rem, 3vw, 1rem);">{status}</p>
            </div>
            """,
            unsafe_allow_html=True
        )


def display_overview_section(loan_data: Dict):
    """Display overview information."""
    st.subheader("Loan Overview")
    
    # Responsive columns: 1 on mobile, 2 on desktop
    cols = get_responsive_columns(mobile=1, tablet=2, desktop=2)
    
    with cols[0]:
        st.markdown("**Loan Type:**")
        st.write(loan_data.get('loan_type', 'N/A').title())
        
        bank_info = loan_data.get('bank_info', {})
        if bank_info:
            st.markdown("**Bank Name:**")
            st.write(bank_info.get('bank_name', 'N/A'))
            
            if bank_info.get('branch_name'):
                st.markdown("**Branch:**")
                st.write(bank_info.get('branch_name'))
    
    if len(cols) > 1:
        with cols[1]:
            st.markdown("**Loan ID:**")
            st.code(loan_data.get('loan_id', 'N/A'), language=None)
            
            st.markdown("**Document ID:**")
            st.code(loan_data.get('document_id', 'N/A'), language=None)
            
            extraction_time = loan_data.get('extraction_timestamp')
            if extraction_time:
                st.markdown("**Extracted On:**")
                st.write(extraction_time)


def display_financial_details(loan_data: Dict):
    """Display financial details section."""
    st.subheader("Core Loan Terms")
    
    # Display key financial metrics in responsive columns
    currency = loan_data.get('currency', 'INR')
    principal = loan_data.get('principal_amount')
    interest_rate = loan_data.get('interest_rate')
    tenure = loan_data.get('tenure_months')
    
    # Prepare metrics data
    metrics = []
    
    if principal is not None:
        metrics.append(("Principal Amount", f"{currency} {principal:,.2f}"))
    else:
        metrics.append(("Principal Amount", "Not Available"))
    
    if interest_rate is not None:
        metrics.append(("Interest Rate", f"{interest_rate:.2f}%"))
    else:
        metrics.append(("Interest Rate", "Not Available"))
    
    if tenure is not None:
        years = tenure // 12
        months = tenure % 12
        tenure_str = f"{years}y {months}m" if years > 0 else f"{months}m"
        metrics.append(("Tenure", tenure_str))
    else:
        metrics.append(("Tenure", "Not Available"))
    
    # Use responsive metrics display
    responsive_metrics(metrics, cols_mobile=1, cols_desktop=3)
    
    st.markdown("---")
    
    # Repayment details with responsive columns
    cols = get_responsive_columns(mobile=1, tablet=2, desktop=2)
    
    with cols[0]:
        st.markdown("**Repayment Mode:**")
        st.write(loan_data.get('repayment_mode', 'N/A'))
        
        moratorium = loan_data.get('moratorium_period_months')
        if moratorium:
            st.markdown("**Moratorium Period:**")
            st.write(f"{moratorium} months")
    
    if len(cols) > 1:
        with cols[1]:
            processing_fee = loan_data.get('processing_fee')
            if processing_fee is not None:
                st.markdown("**Processing Fee:**")
                st.write(f"{currency} {processing_fee:,.2f}")
    
    # Fees section
    fees = loan_data.get('fees', [])
    if fees:
        st.markdown("---")
        st.subheader("Fees & Charges")
        display_fees_table(fees)
    
    # Penalties with responsive columns
    st.markdown("---")
    st.subheader("Penalties")
    
    cols = get_responsive_columns(mobile=1, tablet=2, desktop=2)
    
    with cols[0]:
        late_penalty = loan_data.get('late_payment_penalty')
        if late_penalty:
            st.markdown("**Late Payment Penalty:**")
            st.info(late_penalty)
        else:
            st.markdown("**Late Payment Penalty:**")
            st.write("Not specified")
    
    if len(cols) > 1:
        with cols[1]:
            prepayment_penalty = loan_data.get('prepayment_penalty')
            if prepayment_penalty:
                st.markdown("**Prepayment Penalty:**")
                st.info(prepayment_penalty)
            else:
                st.markdown("**Prepayment Penalty:**")
                st.write("Not specified")


def display_fees_table(fees: List[Dict]):
    """
    Display fees in a formatted table.
    
    Args:
        fees: List of fee items
    """
    if not fees:
        st.write("No fees information available")
        return
    
    # Convert fees to DataFrame
    fees_data = []
    for fee in fees:
        fees_data.append({
            'Fee Type': fee.get('fee_type', 'N/A').title(),
            'Amount': f"{fee.get('currency', 'INR')} {fee.get('amount', 0):,.2f}",
            'Conditions': fee.get('conditions', 'N/A')
        })
    
    df = pd.DataFrame(fees_data)
    mobile_friendly_table(df, max_columns_mobile=2)


def display_tables_section(loan_data: Dict):
    """Display tables and payment schedules."""
    st.subheader("Extracted Tables")
    
    # Payment schedule
    payment_schedule = loan_data.get('payment_schedule', [])
    if payment_schedule:
        st.markdown("### 📅 Payment Schedule")
        display_payment_schedule(payment_schedule)
        st.markdown("---")
    
    # Other tables
    tables = loan_data.get('tables', [])
    if tables:
        st.markdown("### 📊 Additional Tables")
        for idx, table in enumerate(tables):
            display_table_data(table, idx)
    
    if not payment_schedule and not tables:
        st.info("No table data was extracted from this document")


def display_payment_schedule(schedule: List[Dict]):
    """
    Display payment schedule in a formatted table.
    
    Args:
        schedule: List of payment schedule entries
    """
    if not schedule:
        st.write("No payment schedule available")
        return
    
    # Convert schedule to DataFrame
    schedule_data = []
    for entry in schedule:
        row = {
            'Payment #': entry.get('payment_number', 'N/A'),
            'Date': entry.get('payment_date', 'N/A'),
            'Total Amount': f"{entry.get('total_amount', 0):,.2f}",
        }
        
        # Add optional columns if available
        if entry.get('principal_component') is not None:
            row['Principal'] = f"{entry.get('principal_component', 0):,.2f}"
        
        if entry.get('interest_component') is not None:
            row['Interest'] = f"{entry.get('interest_component', 0):,.2f}"
        
        if entry.get('outstanding_balance') is not None:
            row['Outstanding'] = f"{entry.get('outstanding_balance', 0):,.2f}"
        
        schedule_data.append(row)
    
    df = pd.DataFrame(schedule_data)
    mobile_friendly_table(df, max_columns_mobile=3)
    
    # Show summary statistics
    if len(schedule) > 0:
        total_payments = sum(entry.get('total_amount', 0) for entry in schedule)
        st.caption(f"Total of {len(schedule)} payments | Total Amount: {total_payments:,.2f}")


def display_table_data(table: Dict, index: int):
    """
    Display a generic table with proper formatting.
    
    Args:
        table: Table data dictionary
        index: Table index for display
    """
    table_type = table.get('table_type', 'other')
    table_id = table.get('table_id', f'table_{index}')
    
    with st.expander(f"Table {index + 1}: {table_type.replace('_', ' ').title()}", expanded=False):
        headers = table.get('headers', [])
        rows = table.get('rows', [])
        
        if not headers or not rows:
            st.write("No data available for this table")
            return
        
        # Create DataFrame from headers and rows
        try:
            df = pd.DataFrame(rows, columns=headers)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Show nested columns if available
            nested_columns = table.get('nested_columns')
            if nested_columns:
                st.markdown("**Nested Column Structure:**")
                st.json(nested_columns)
        
        except Exception as e:
            st.error(f"Error displaying table: {str(e)}")
            st.write("Raw table data:")
            st.json(table)


def display_additional_info(loan_data: Dict):
    """Display additional loan information."""
    st.subheader("Additional Details")
    
    # Co-signer information with responsive columns
    co_signer = loan_data.get('co_signer')
    if co_signer:
        st.markdown("### 👥 Co-signer Information")
        cols = get_responsive_columns(mobile=1, tablet=2, desktop=2)
        
        with cols[0]:
            st.markdown("**Name:**")
            st.write(co_signer.get('name', 'N/A'))
            
            st.markdown("**Relationship:**")
            st.write(co_signer.get('relationship', 'N/A'))
        
        if len(cols) > 1:
            with cols[1]:
                contact = co_signer.get('contact')
                if contact:
                    st.markdown("**Contact:**")
                    st.write(contact)
        
        st.markdown("---")
    
    # Collateral details
    collateral = loan_data.get('collateral_details')
    if collateral:
        st.markdown("### 🏦 Collateral Details")
        st.info(collateral)
        st.markdown("---")
    
    # Disbursement terms
    disbursement = loan_data.get('disbursement_terms')
    if disbursement:
        st.markdown("### 💸 Disbursement Terms")
        st.info(disbursement)
        st.markdown("---")
    
    # Raw extracted fields (for debugging/transparency)
    raw_fields = loan_data.get('raw_extracted_fields', {})
    if raw_fields:
        with st.expander("🔍 View Raw Extracted Fields", expanded=False):
            st.json(raw_fields)
    
    # Show message if no additional info
    if not co_signer and not collateral and not disbursement and not raw_fields:
        st.info("No additional information available for this loan")
