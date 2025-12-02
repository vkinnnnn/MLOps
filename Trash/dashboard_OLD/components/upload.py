"""
Upload interface component for the dashboard
"""
import streamlit as st
from typing import Any
import sys
import os
from datetime import datetimeme
from components.responsive_utils import (
    get_responsive_columns,
    mobile_friendly_table,
    responsive_button_group
)

def render_upload_interface(api_client):
    """
    Render the document upload interface with drag-and-drop support
    
    Args:
        api_client: APIClient instance for backend communication
    """
    
    st.markdown("### 📤 Upload Documents")
    
    # File uploader with drag-and-drop
    uploaded_files = st.file_uploader(
        "Drag and drop files here or click to browse",
        type=["pdf", "jpg", "jpeg", "png", "tiff", "tif"],
        accept_multiple_files=True,
        help="Supported formats: PDF, JPEG, PNG, TIFF (Max 200MB per file)"
    )
    
    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file(s) selected**")
        
        # Display file details
        with st.expander("📋 File Details", expanded=True):
            for idx, file in enumerate(uploaded_files, 1):
                # Use responsive columns: 1 column on mobile, 3 on desktop
                cols = get_responsive_columns(mobile=1, tablet=2, desktop=3)
                
                if len(cols) == 1:
                    # Mobile layout - stack vertically
                    with cols[0]:
                        st.text(f"{idx}. {file.name}")
                        file_size_mb = file.size / (1024 * 1024)
                        st.caption(f"Size: {file_size_mb:.2f} MB | Type: {file.type.split('/')[-1].upper()}")
                else:
                    # Desktop/Tablet layout - horizontal
                    with cols[0]:
                        st.text(f"{idx}. {file.name}")
                    with cols[1]:
                        file_size_mb = file.size / (1024 * 1024)
                        st.text(f"{file_size_mb:.2f} MB")
                    if len(cols) > 2:
                        with cols[2]:
                            st.text(file.type.split('/')[-1].upper())
        
        # Upload button - full width on mobile, centered on desktop
        cols = get_responsive_columns(mobile=1, tablet=1, desktop=3)
        if len(cols) == 3:
            with cols[1]:
                if st.button("🚀 Process Documents", type="primary", use_container_width=True):
                    process_uploads(uploaded_files, api_client)
        else:
            with cols[0]:
                if st.button("🚀 Process Documents", type="primary", use_container_width=True):
                    process_uploads(uploaded_files, api_client)
    
    # Display upload history
    if st.session_state.uploaded_documents:
        st.markdown("---")
        st.markdown("### 📚 Recent Uploads")
        display_upload_history()

def process_uploads(files: List, api_client):
    """
    Process uploaded files and display progress
    
    Args:
        files: List of uploaded file objects
        api_client: APIClient instance
    """
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_files = len(files)
    successful_uploads = []
    failed_uploads = []
    
    for idx, file in enumerate(files):
        try:
            # Update progress
            progress = (idx + 1) / total_files
            progress_bar.progress(progress)
            status_text.text(f"Processing {file.name}... ({idx + 1}/{total_files})")
            
            # Reset file pointer
            file.seek(0)
            
            # Upload to backend
            response = api_client.upload_document(file)
            
            # Store in session state
            upload_info = {
                "file_name": file.name,
                "document_id": response.get("document_id"),
                "upload_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": response.get("status", "processing"),
                "file_size": file.size
            }
            successful_uploads.append(upload_info)
            
        except Exception as e:
            failed_uploads.append({
                "file_name": file.name,
                "error": str(e)
            })
    
    # Update session state
    st.session_state.uploaded_documents.extend(successful_uploads)
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Display results
    display_upload_results(successful_uploads, failed_uploads)

def display_upload_results(successful: List[dict], failed: List[dict]):
    """
    Display upload results with success and error messages
    
    Args:
        successful: List of successfully uploaded documents
        failed: List of failed uploads with error messages
    """
    
    if successful:
        st.success(f"✅ Successfully uploaded {len(successful)} document(s)")
        
        with st.expander("View uploaded documents"):
            for doc in successful:
                st.markdown(f"- **{doc['file_name']}** (ID: `{doc['document_id']}`)")
    
    if failed:
        st.error(f"❌ Failed to upload {len(failed)} document(s)")
        
        with st.expander("View errors"):
            for doc in failed:
                st.markdown(f"- **{doc['file_name']}**: {doc['error']}")

def display_upload_history():
    """Display history of uploaded documents"""
    
    if not st.session_state.uploaded_documents:
        st.info("No documents uploaded yet")
        return
    
                    st.session_state.uploaded_documents.append({
                        "name": file.name,
                        "size": file.size,
                        "type": file.type,
                        "content": file_content,
                        "extracted_data": masked_data,  # For display (privacy protected)
                        "extracted_data_unmasked": unmasked_data,  # For download (full details)
                        "upload_date": datetime.now().date()  # Add upload date for filtering
                    })0]:
                st.markdown(f"**{doc['file_name']}**")
                st.caption(f"Uploaded: {doc['upload_time']}")
                status_emoji = "✅" if doc["status"] == "completed" else "⏳"
                st.caption(f"Status: {status_emoji} {doc['status']}")
                if st.button("View Details", key=f"view_{doc['document_id']}", use_container_width=True):
                    st.session_state.selected_document = doc["document_id"]
                    st.session_state.current_view = "view"
                    st.rerun()
                st.markdown("---")
        else:
            # Desktop/Tablet layout - horizontal
            with cols[0]:
                st.text(doc["file_name"])
            if len(cols) >= 2:
                with cols[1]:
                    st.text(doc["upload_time"])
            if len(cols) >= 3:
                with cols[2]:
                    status_emoji = "✅" if doc["status"] == "completed" else "⏳"
                    st.text(f"{status_emoji} {doc['status']}")
            if len(cols) >= 4:
                with cols[3]:
                    if st.button("View", key=f"view_{doc['document_id']}"):
                        st.session_state.selected_document = doc["document_id"]
                        st.session_state.current_view = "view"
                        st.rerun()
