"""
Search and filtering component for the dashboard
Enables document search, filtering, and sorting
"""
import streamlit as st
from typing import Any, Dict, List, Optional
from datetime import datetime, date
import pandas as pd


def render_search_interface(api_client: Any):
    """
    Render the search and filtering interface
    
    Args:
        api_client: API client instance for backend communication
    """
    st.subheader("🔍 Search & Filter Loans")
    
    # Check if there are any uploaded documents
    if "uploaded_documents" not in st.session_state or not st.session_state.uploaded_documents:
        st.info("👆 No documents uploaded yet. Please upload documents first.")
        if st.button("Go to Upload"):
            st.session_state.current_view = "upload"
            st.rerun()
        return
    
    st.markdown("---")
    
    # Search and filter controls
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Search bar
        search_query = st.text_input(
            "🔍 Search documents",
            placeholder="Search by filename, bank name, or loan type...",
            help="Enter keywords to search across document names and extracted data"
        )
    
    with col2:
        # Quick stats
        total_docs = len(st.session_state.uploaded_documents)
        processed_docs = len([d for d in st.session_state.uploaded_documents if "extracted_data" in d])
        st.metric("Total Documents", total_docs)
        st.caption(f"{processed_docs} processed")
    
    st.markdown("---")
    
    # Filter controls
    st.markdown("### 🎛️ Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Loan type filter
        loan_types = get_unique_values("loan_type")
        selected_loan_types = st.multiselect(
            "Loan Type",
            options=["All"] + loan_types,
            default=["All"],
            help="Filter by loan type"
        )
    
    with col2:
        # Bank name filter
        bank_names = get_unique_values("bank_name")
        selected_banks = st.multiselect(
            "Bank Name",
            options=["All"] + bank_names,
            default=["All"],
            help="Filter by lending institution"
        )
    
    with col3:
        # Amount range filter
        st.markdown("**Principal Amount**")
        min_amount, max_amount = get_amount_range()
        amount_range = st.slider(
            "Amount Range",
            min_value=float(min_amount),
            max_value=float(max_amount),
            value=(float(min_amount), float(max_amount)),
            format="$%.0f",
            label_visibility="collapsed"
        )
    
    with col4:
        # Date range filter
        st.markdown("**Upload Date**")
        date_filter = st.selectbox(
            "Date Range",
            options=["All Time", "Today", "Last 7 Days", "Last 30 Days", "Custom"],
            label_visibility="collapsed"
        )
    
    # Custom date range
    if date_filter == "Custom":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From", value=date.today())
        with col2:
            end_date = st.date_input("To", value=date.today())
    else:
        start_date = None
        end_date = None
    
    st.markdown("---")
    
    # Sorting controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        sort_by = st.selectbox(
            "Sort by",
            options=["Upload Date (Newest)", "Upload Date (Oldest)", "Principal Amount (High to Low)", 
                    "Principal Amount (Low to High)", "Bank Name (A-Z)", "Bank Name (Z-A)", 
                    "Interest Rate (High to Low)", "Interest Rate (Low to High)"]
        )
    
    with col2:
        items_per_page = st.selectbox(
            "Items per page",
            options=[10, 25, 50, 100],
            index=0
        )
    
    with col3:
        if st.button("🔄 Reset Filters", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # Apply filters and search
    filtered_docs = apply_filters_and_search(
        search_query=search_query,
        loan_types=selected_loan_types,
        banks=selected_banks,
        amount_range=amount_range,
        date_filter=date_filter,
        start_date=start_date,
        end_date=end_date
    )
    
    # Apply sorting
    sorted_docs = apply_sorting(filtered_docs, sort_by)
    
    # Display results with pagination
    display_paginated_results(sorted_docs, items_per_page)


def get_unique_values(field: str) -> List[str]:
    """
    Get unique values for a field from all documents
    
    Args:
        field: Field name to extract unique values from
        
    Returns:
        List of unique values
    """
    if "uploaded_documents" not in st.session_state:
        return []
    
    values = set()
    for doc in st.session_state.uploaded_documents:
        extracted_data = doc.get("extracted_data", {})
        if extracted_data and field in extracted_data:
            value = extracted_data[field]
            if value:
                values.add(str(value))
    
    return sorted(list(values))


def get_amount_range() -> tuple:
    """
    Get min and max principal amounts from all documents
    
    Returns:
        Tuple of (min_amount, max_amount)
    """
    if "uploaded_documents" not in st.session_state:
        return (0, 100000)
    
    amounts = []
    for doc in st.session_state.uploaded_documents:
        extracted_data = doc.get("extracted_data", {})
        if extracted_data and "principal_amount" in extracted_data:
            amount = extracted_data.get("principal_amount", 0)
            if amount > 0:
                amounts.append(amount)
    
    if not amounts:
        return (0, 100000)
    
    return (min(amounts), max(amounts))


def apply_filters_and_search(
    search_query: str,
    loan_types: List[str],
    banks: List[str],
    amount_range: tuple,
    date_filter: str,
    start_date: Optional[date],
    end_date: Optional[date]
) -> List[Dict[str, Any]]:
    """
    Apply filters and search to documents
    
    Args:
        search_query: Search query string
        loan_types: Selected loan types
        banks: Selected banks
        amount_range: Tuple of (min, max) amount
        date_filter: Date filter option
        start_date: Custom start date
        end_date: Custom end date
        
    Returns:
        Filtered list of documents
    """
    if "uploaded_documents" not in st.session_state:
        return []
    
    filtered = st.session_state.uploaded_documents.copy()
    
    # Apply search query
    if search_query:
        query_lower = search_query.lower()
        filtered = [
            doc for doc in filtered
            if query_lower in doc["name"].lower() or
            query_lower in doc.get("extracted_data", {}).get("bank_name", "").lower() or
            query_lower in doc.get("extracted_data", {}).get("loan_type", "").lower()
        ]
    
    # Apply loan type filter
    if "All" not in loan_types and loan_types:
        filtered = [
            doc for doc in filtered
            if doc.get("extracted_data", {}).get("loan_type") in loan_types
        ]
    
    # Apply bank filter
    if "All" not in banks and banks:
        filtered = [
            doc for doc in filtered
            if doc.get("extracted_data", {}).get("bank_name") in banks
        ]
    
    # Apply amount range filter
    filtered = [
        doc for doc in filtered
        if amount_range[0] <= doc.get("extracted_data", {}).get("principal_amount", 0) <= amount_range[1]
    ]
    
    # Apply date filter
    if date_filter != "All Time":
        today = datetime.now().date()
        
        if date_filter == "Today":
            filtered = [
                doc for doc in filtered
                if doc.get("upload_date", today) == today
            ]
        elif date_filter == "Last 7 Days":
            from datetime import timedelta
            week_ago = today - timedelta(days=7)
            filtered = [
                doc for doc in filtered
                if doc.get("upload_date", today) >= week_ago
            ]
        elif date_filter == "Last 30 Days":
            from datetime import timedelta
            month_ago = today - timedelta(days=30)
            filtered = [
                doc for doc in filtered
                if doc.get("upload_date", today) >= month_ago
            ]
        elif date_filter == "Custom" and start_date and end_date:
            filtered = [
                doc for doc in filtered
                if start_date <= doc.get("upload_date", today) <= end_date
            ]
    
    return filtered


def apply_sorting(docs: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
    """
    Apply sorting to documents
    
    Args:
        docs: List of documents
        sort_by: Sort option
        
    Returns:
        Sorted list of documents
    """
    if not docs:
        return docs
    
    if sort_by == "Upload Date (Newest)":
        return sorted(docs, key=lambda d: d.get("upload_date", date.today()), reverse=True)
    elif sort_by == "Upload Date (Oldest)":
        return sorted(docs, key=lambda d: d.get("upload_date", date.today()))
    elif sort_by == "Principal Amount (High to Low)":
        return sorted(docs, key=lambda d: d.get("extracted_data", {}).get("principal_amount", 0), reverse=True)
    elif sort_by == "Principal Amount (Low to High)":
        return sorted(docs, key=lambda d: d.get("extracted_data", {}).get("principal_amount", 0))
    elif sort_by == "Bank Name (A-Z)":
        return sorted(docs, key=lambda d: d.get("extracted_data", {}).get("bank_name", ""))
    elif sort_by == "Bank Name (Z-A)":
        return sorted(docs, key=lambda d: d.get("extracted_data", {}).get("bank_name", ""), reverse=True)
    elif sort_by == "Interest Rate (High to Low)":
        return sorted(docs, key=lambda d: d.get("extracted_data", {}).get("interest_rate", 0), reverse=True)
    elif sort_by == "Interest Rate (Low to High)":
        return sorted(docs, key=lambda d: d.get("extracted_data", {}).get("interest_rate", 0))
    
    return docs


def display_paginated_results(docs: List[Dict[str, Any]], items_per_page: int):
    """
    Display paginated search results
    
    Args:
        docs: List of documents to display
        items_per_page: Number of items per page
    """
    if not docs:
        st.info("No documents match your search criteria")
        return
    
    # Calculate pagination
    total_items = len(docs)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    # Page selector
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            current_page = st.selectbox(
                "Page",
                options=list(range(1, total_pages + 1)),
                format_func=lambda x: f"Page {x} of {total_pages}",
                key="search_page"
            )
    else:
        current_page = 1
    
    # Calculate slice indices
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    # Display results count
    st.markdown(f"### 📄 Results ({total_items} documents found)")
    st.caption(f"Showing {start_idx + 1}-{end_idx} of {total_items}")
    
    st.markdown("---")
    
    # Display documents
    page_docs = docs[start_idx:end_idx]
    
    for doc in page_docs:
        display_document_card(doc)


def display_document_card(doc: Dict[str, Any]):
    """
    Display a document card with key information
    
    Args:
        doc: Document dictionary
    """
    extracted_data = doc.get("extracted_data", {})
    
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            st.markdown(f"**📄 {doc['name']}**")
            bank = extracted_data.get("bank_name", "Unknown Bank")
            loan_type = extracted_data.get("loan_type", "Unknown Type")
            st.caption(f"{bank} • {loan_type}")
        
        with col2:
            principal = extracted_data.get("principal_amount", 0)
            st.metric("Principal", f"${principal:,.2f}")
        
        with col3:
            interest_rate = extracted_data.get("interest_rate", 0)
            tenure = extracted_data.get("tenure_months", 0)
            st.metric("Rate / Tenure", f"{interest_rate}% / {tenure}m")
        
        with col4:
            if st.button("View", key=f"view_{doc['name']}", use_container_width=True):
                st.session_state.selected_document = doc["name"]
                st.session_state.current_view = "data_viewer"
                st.rerun()
        
        # Additional info in expander
        with st.expander("More Details"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Processing Fee:** ${extracted_data.get('processing_fee', 0):,.2f}")
                st.write(f"**Moratorium:** {extracted_data.get('moratorium_period_months', 0)} months")
            
            with col2:
                st.write(f"**Monthly EMI:** ${extracted_data.get('monthly_emi', 0):,.2f}")
                st.write(f"**Prepayment:** {extracted_data.get('prepayment_penalty', 'N/A')}")
            
            with col3:
                confidence = extracted_data.get("extraction_confidence", 0.95)
                st.write(f"**Confidence:** {confidence * 100:.1f}%")
                upload_date = doc.get("upload_date", date.today())
                st.write(f"**Uploaded:** {upload_date}")
        
        st.markdown("---")


def render_quick_search(api_client: Any):
    """
    Render a quick search bar (compact version)
    
    Args:
        api_client: API client instance
    """
    search_query = st.text_input(
        "🔍 Quick Search",
        placeholder="Search documents...",
        key="quick_search"
    )
    
    if search_query:
        # Perform quick search
        filtered_docs = apply_filters_and_search(
            search_query=search_query,
            loan_types=["All"],
            banks=["All"],
            amount_range=(0, float('inf')),
            date_filter="All Time",
            start_date=None,
            end_date=None
        )
        
        if filtered_docs:
            st.success(f"Found {len(filtered_docs)} matching documents")
            for doc in filtered_docs[:5]:  # Show top 5
                if st.button(f"📄 {doc['name']}", key=f"quick_{doc['name']}"):
                    st.session_state.selected_document = doc["name"]
                    st.session_state.current_view = "data_viewer"
                    st.rerun()
        else:
            st.info("No matching documents found")
