"""
Document management component for the dashboard
Displays document list, processing status, and management actions
"""
import streamlit as st
from typing import Any, Dict, List, Optional
from datetime import datetime, date
import pandas as pd


def render_document_manager(api_client: Any):
    """
    Render the document management interface
    
    Args:
        api_client: API client instance for backend communication
    """
    st.subheader("📁 Document Management")
    
    # Check if there are any uploaded documents
    if "uploaded_documents" not in st.session_state or not st.session_state.uploaded_documents:
        st.info("👆 No documents uploaded yet. Please upload documents first.")
        if st.button("Go to Upload"):
            st.session_state.current_view = "upload"
            st.rerun()
        return
    
    st.markdown("---")
    
    # Summary statistics
    display_summary_stats()
    
    st.markdown("---")
    
    # Document list with status
    st.markdown("### 📋 Document List")
    
    # View mode selector
    view_mode = st.radio(
        "View Mode",
        options=["Card View", "Table View"],
        horizontal=True
    )
    
    if view_mode == "Card View":
        display_card_view()
    else:
        display_table_view()


def display_summary_stats():
    """Display summary statistics for all documents"""
    docs = st.session_state.uploaded_documents
    
    total_docs = len(docs)
    processed_docs = len([d for d in docs if d.get("extracted_data")])
    pending_docs = total_docs - processed_docs
    
    # Calculate total size
    total_size = sum(d.get("size", 0) for d in docs) / (1024 * 1024)  # Convert to MB
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Documents", total_docs)
    
    with col2:
        st.metric("Processed", processed_docs, delta=f"{(processed_docs/total_docs*100):.0f}%" if total_docs > 0 else "0%")
    
    with col3:
        st.metric("Pending", pending_docs)
    
    with col4:
        st.metric("Total Size", f"{total_size:.2f} MB")


def display_card_view():
    """Display documents in card view"""
    docs = st.session_state.uploaded_documents
    
    for doc in docs:
        display_document_management_card(doc)


def display_table_view():
    """Display documents in table view"""
    docs = st.session_state.uploaded_documents
    
    # Prepare table data
    table_data = []
    for doc in docs:
        extracted_data = doc.get("extracted_data", {})
        
        status = "✅ Processed" if extracted_data else "⏳ Pending"
        confidence = extracted_data.get("extraction_confidence", 0) if extracted_data else 0
        
        table_data.append({
            "Document": doc["name"],
            "Status": status,
            "Bank": extracted_data.get("bank_name", "N/A") if extracted_data else "N/A",
            "Type": extracted_data.get("loan_type", "N/A") if extracted_data else "N/A",
            "Principal": f"${extracted_data.get('principal_amount', 0):,.2f}" if extracted_data else "N/A",
            "Confidence": f"{confidence * 100:.1f}%" if confidence > 0 else "N/A",
            "Size": f"{doc.get('size', 0) / 1024:.2f} KB",
            "Upload Date": str(doc.get("upload_date", date.today()))
        })
    
    df = pd.DataFrame(table_data)
    
    # Display table with selection
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Confidence": st.column_config.TextColumn("Confidence", width="small"),
        }
    )
    
    # Action buttons for selected documents
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh All", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("📊 Compare All Processed", use_container_width=True):
            st.session_state.current_view = "compare"
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear All", use_container_width=True, type="secondary"):
            if st.session_state.get("confirm_clear_all"):
                st.session_state.uploaded_documents = []
                st.session_state.confirm_clear_all = False
                st.success("All documents cleared")
                st.rerun()
            else:
                st.session_state.confirm_clear_all = True
                st.warning("Click again to confirm deletion of all documents")


def display_document_management_card(doc: Dict[str, Any]):
    """
    Display a document management card
    
    Args:
        doc: Document dictionary
    """
    extracted_data = doc.get("extracted_data", {})
    has_data = bool(extracted_data)
    
    with st.container():
        # Header row
        col1, col2, col3 = st.columns([4, 1, 1])
        
        with col1:
            st.markdown(f"### 📄 {doc['name']}")
        
        with col2:
            # Processing status
            if has_data:
                st.success("✅ Processed")
            else:
                st.warning("⏳ Pending")
        
        with col3:
            # Delete button
            if st.button("🗑️", key=f"delete_{doc['name']}", help="Delete document"):
                delete_document(doc["name"])
        
        # Document details
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.write(f"**Size:** {doc.get('size', 0) / 1024:.2f} KB")
            st.write(f"**Type:** {doc.get('type', 'Unknown')}")
        
        with col2:
            if has_data:
                bank = extracted_data.get("bank_name", "Unknown")
                loan_type = extracted_data.get("loan_type", "Unknown")
                st.write(f"**Bank:** {bank}")
                st.write(f"**Loan Type:** {loan_type}")
            else:
                st.write("**Bank:** Processing...")
                st.write("**Loan Type:** Processing...")
        
        with col3:
            if has_data:
                principal = extracted_data.get("principal_amount", 0)
                interest_rate = extracted_data.get("interest_rate", 0)
                st.write(f"**Principal:** ${principal:,.2f}")
                st.write(f"**Rate:** {interest_rate}%")
            else:
                st.write("**Principal:** -")
                st.write("**Rate:** -")
        
        with col4:
            if has_data:
                confidence = extracted_data.get("extraction_confidence", 0)
                confidence_color = get_confidence_color(confidence)
                st.write(f"**Confidence:** {confidence * 100:.1f}%")
                st.progress(confidence)
            else:
                st.write("**Confidence:** -")
                st.write("Processing...")
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("👁️ View Details", key=f"view_{doc['name']}", use_container_width=True):
                st.session_state.selected_document = doc["name"]
                st.session_state.current_view = "data_viewer"
                st.rerun()
        
        with col2:
            if has_data:
                if st.button("📊 Compare", key=f"compare_{doc['name']}", use_container_width=True):
                    st.session_state.current_view = "compare"
                    st.rerun()
            else:
                st.button("📊 Compare", disabled=True, use_container_width=True)
        
        with col3:
            if has_data:
                # Download extracted data
                import json
                json_data = json.dumps(extracted_data, indent=2)
                st.download_button(
                    label="📥 JSON",
                    data=json_data,
                    file_name=f"{doc['name']}_data.json",
                    mime="application/json",
                    key=f"download_json_{doc['name']}",
                    use_container_width=True
                )
            else:
                st.button("📥 JSON", disabled=True, use_container_width=True)
        
        with col4:
            if "content" in doc:
                st.download_button(
                    label="📑 Original",
                    data=doc["content"],
                    file_name=doc["name"],
                    mime=doc.get("type", "application/pdf"),
                    key=f"download_orig_{doc['name']}",
                    use_container_width=True
                )
            else:
                st.button("📑 Original", disabled=True, use_container_width=True)
        
        with col5:
            if st.button("🔄 Reprocess", key=f"reprocess_{doc['name']}", use_container_width=True):
                reprocess_document(doc)
        
        # Show confidence breakdown if available
        if has_data and confidence < 0.85:
            st.warning(f"⚠️ Low confidence score ({confidence * 100:.1f}%). Please review extracted data carefully.")
        
        st.markdown("---")


def get_confidence_color(confidence: float) -> str:
    """
    Get color for confidence score
    
    Args:
        confidence: Confidence score (0-1)
        
    Returns:
        Color string
    """
    if confidence >= 0.95:
        return "green"
    elif confidence >= 0.90:
        return "blue"
    elif confidence >= 0.85:
        return "orange"
    else:
        return "red"


def delete_document(doc_name: str):
    """
    Delete a document from the session state
    
    Args:
        doc_name: Name of document to delete
    """
    if "uploaded_documents" not in st.session_state:
        return
    
    # Confirm deletion
    confirm_key = f"confirm_delete_{doc_name}"
    
    if st.session_state.get(confirm_key):
        # Actually delete
        st.session_state.uploaded_documents = [
            doc for doc in st.session_state.uploaded_documents 
            if doc["name"] != doc_name
        ]
        st.session_state[confirm_key] = False
        st.success(f"Deleted {doc_name}")
        st.rerun()
    else:
        # Ask for confirmation
        st.session_state[confirm_key] = True
        st.warning(f"Click delete again to confirm deletion of {doc_name}")


def reprocess_document(doc: Dict[str, Any]):
    """
    Reprocess a document
    
    Args:
        doc: Document dictionary
    """
    with st.spinner(f"Reprocessing {doc['name']}..."):
        try:
            # Call API to reprocess
            import requests
            
            api_base_url = st.session_state.get("api_base_url", "http://api:8000")
            
            if "content" in doc:
                files = {"file": (doc["name"], doc["content"], doc.get("type", "application/pdf"))}
                response = requests.post(
                    f"{api_base_url}/api/v1/extract",
                    files=files,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Update document in session state
                    for i, d in enumerate(st.session_state.uploaded_documents):
                        if d["name"] == doc["name"]:
                            st.session_state.uploaded_documents[i]["extracted_data"] = result
                            break
                    
                    st.success(f"✓ Reprocessed {doc['name']}")
                    st.rerun()
                else:
                    st.error(f"Failed to reprocess: {response.text}")
            else:
                st.error("Document content not available for reprocessing")
                
        except Exception as e:
            st.error(f"Error reprocessing document: {str(e)}")


def display_processing_status(doc: Dict[str, Any]):
    """
    Display detailed processing status for a document
    
    Args:
        doc: Document dictionary
    """
    st.markdown("#### 🔄 Processing Status")
    
    extracted_data = doc.get("extracted_data", {})
    
    if not extracted_data:
        st.info("Document is pending processing")
        st.progress(0)
        return
    
    # Show processing stages
    stages = [
        ("Upload", True, "✅"),
        ("OCR Processing", True, "✅"),
        ("Data Extraction", True, "✅"),
        ("Validation", True, "✅"),
        ("Complete", True, "✅")
    ]
    
    for stage_name, completed, icon in stages:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"{icon} {stage_name}")
        with col2:
            if completed:
                st.write("Complete")
    
    st.progress(1.0)
    
    # Show extraction confidence breakdown
    st.markdown("#### 📊 Extraction Confidence")
    
    confidence = extracted_data.get("extraction_confidence", 0.95)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.progress(confidence)
    
    with col2:
        st.metric("Overall", f"{confidence * 100:.1f}%")
    
    # Show field-level confidence if available
    if "field_confidences" in extracted_data:
        st.markdown("##### Field Confidence Scores")
        field_confs = extracted_data["field_confidences"]
        
        for field, conf in field_confs.items():
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(field.replace("_", " ").title())
            with col2:
                st.write(f"{conf * 100:.1f}%")


def render_document_detail_view(doc_name: str):
    """
    Render detailed view for a specific document
    
    Args:
        doc_name: Name of document to display
    """
    if "uploaded_documents" not in st.session_state:
        st.error("No documents available")
        return
    
    # Find document
    doc = next((d for d in st.session_state.uploaded_documents if d["name"] == doc_name), None)
    
    if not doc:
        st.error(f"Document '{doc_name}' not found")
        return
    
    # Display document header
    st.markdown(f"# 📄 {doc['name']}")
    
    # Back button
    if st.button("← Back to Document List"):
        st.session_state.current_view = "document_manager"
        st.rerun()
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 Overview", "🔄 Processing Status", "📊 Extracted Data"])
    
    with tab1:
        display_document_overview(doc)
    
    with tab2:
        display_processing_status(doc)
    
    with tab3:
        extracted_data = doc.get("extracted_data", {})
        if extracted_data:
            st.json(extracted_data)
        else:
            st.info("No extracted data available yet")


def display_document_overview(doc: Dict[str, Any]):
    """
    Display document overview
    
    Args:
        doc: Document dictionary
    """
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📁 File Information")
        st.write(f"**Filename:** {doc['name']}")
        st.write(f"**Size:** {doc.get('size', 0) / 1024:.2f} KB")
        st.write(f"**Type:** {doc.get('type', 'Unknown')}")
        st.write(f"**Upload Date:** {doc.get('upload_date', date.today())}")
    
    with col2:
        st.markdown("### 💰 Loan Information")
        extracted_data = doc.get("extracted_data", {})
        
        if extracted_data:
            st.write(f"**Bank:** {extracted_data.get('bank_name', 'N/A')}")
            st.write(f"**Loan Type:** {extracted_data.get('loan_type', 'N/A')}")
            st.write(f"**Principal:** ${extracted_data.get('principal_amount', 0):,.2f}")
            st.write(f"**Interest Rate:** {extracted_data.get('interest_rate', 0)}%")
        else:
            st.info("Processing...")
