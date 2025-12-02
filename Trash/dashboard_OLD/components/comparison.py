"""
Loan comparison component for the dashboard
Enables multi-document selection and side-by-side comparison
"""
import streamlit as st
from typing import Any, Dict, List, Optional
import pandas as pd
import requests
import json


def render_comparison_interface(api_client: Any):
    """
    Render the loan comparison interface
    
    Args:
        api_client: API client instance for backend communication
    """
    st.subheader("📊 Loan Comparison")
    
    # Check if there are any uploaded documents
    if "uploaded_documents" not in st.session_state or not st.session_state.uploaded_documents:
        st.info("👆 No documents uploaded yet. Please upload at least 2 loan documents to compare.")
        if st.button("Go to Upload"):
            st.session_state.current_view = "upload"
            st.rerun()
        return
    
    # Filter documents that have extracted data
    documents_with_data = [
        doc for doc in st.session_state.uploaded_documents 
        if "extracted_data" in doc and doc.get("extracted_data")
    ]
    
    if len(documents_with_data) < 2:
        st.warning(f"⚠️ You need at least 2 processed documents to compare. Currently have {len(documents_with_data)} processed.")
        st.info("Please upload and process more documents, or wait for current documents to finish processing.")
        return
    
    st.markdown("---")
    
    # Multi-document selection
    st.markdown("### 📋 Select Loans to Compare")
    st.caption("Select 2 or more loan documents to compare side-by-side")
    
    # Create selection checkboxes
    selected_docs = []
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        for doc in documents_with_data:
            extracted_data = doc.get("extracted_data", {})
            bank_name = extracted_data.get("bank_name", "Unknown Bank")
            loan_type = extracted_data.get("loan_type", "Unknown Type")
            principal = extracted_data.get("principal_amount", 0)
            
            label = f"{doc['name']} - {bank_name} ({loan_type}) - ${principal:,.2f}"
            
            if st.checkbox(label, key=f"compare_{doc['name']}"):
                selected_docs.append(doc)
    
    with col2:
        st.metric("Selected", len(selected_docs))
        st.caption(f"Min: 2\nMax: {len(documents_with_data)}")
    
    if len(selected_docs) < 2:
        st.info("👆 Please select at least 2 loans to compare")
        return
    
    st.markdown("---")
    
    # Compare button
    if st.button("🔍 Compare Selected Loans", type="primary", use_container_width=True):
        compare_loans(selected_docs)


def compare_loans(selected_docs: List[Dict[str, Any]]):
    """
    Compare selected loans and display results
    
    Args:
        selected_docs: List of selected document dictionaries
    """
    with st.spinner("🔄 Comparing loans..."):
        try:
            # Prepare loan data for comparison
            loan_data_list = []
            for doc in selected_docs:
                extracted_data = doc.get("extracted_data", {})
                # Use unmasked data if available for accurate comparison
                if "extracted_data_unmasked" in doc:
                    extracted_data = doc["extracted_data_unmasked"]
                loan_data_list.append(extracted_data)
            
            # Call comparison API endpoint
            api_base_url = st.session_state.get("api_base_url", "http://api:8000")
            
            try:
                response = requests.post(
                    f"{api_base_url}/api/v1/compare",
                    json=loan_data_list,
                    timeout=30
                )
                
                if response.status_code == 200:
                    comparison_result = response.json()
                    display_comparison_results(comparison_result, selected_docs)
                else:
                    # Fallback to local comparison if API not available
                    st.warning("⚠️ API comparison not available, using local comparison")
                    local_comparison_result = perform_local_comparison(selected_docs)
                    display_comparison_results(local_comparison_result, selected_docs)
                    
            except requests.exceptions.RequestException:
                # Fallback to local comparison
                st.info("ℹ️ Using local comparison (API not available)")
                local_comparison_result = perform_local_comparison(selected_docs)
                display_comparison_results(local_comparison_result, selected_docs)
                
        except Exception as e:
            st.error(f"❌ Comparison failed: {str(e)}")


def perform_local_comparison(selected_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform local comparison when API is not available
    
    Args:
        selected_docs: List of selected document dictionaries
        
    Returns:
        Comparison result dictionary
    """
    loans = []
    metrics = []
    
    for doc in selected_docs:
        extracted_data = doc.get("extracted_data", {})
        if "extracted_data_unmasked" in doc:
            extracted_data = doc["extracted_data_unmasked"]
        
        # Extract key fields
        principal = extracted_data.get("principal_amount", 0)
        interest_rate = extracted_data.get("interest_rate", 0)
        tenure_months = extracted_data.get("tenure_months", 0)
        processing_fee = extracted_data.get("processing_fee", 0)
        moratorium_months = extracted_data.get("moratorium_period_months", 0)
        
        # Calculate metrics
        monthly_rate = interest_rate / 100 / 12
        if monthly_rate > 0 and tenure_months > 0:
            monthly_emi = principal * monthly_rate * (1 + monthly_rate) ** tenure_months / ((1 + monthly_rate) ** tenure_months - 1)
        else:
            monthly_emi = principal / tenure_months if tenure_months > 0 else 0
        
        total_amount = monthly_emi * tenure_months
        total_interest = total_amount - principal
        total_cost = total_amount + processing_fee
        effective_rate = (total_interest / principal * 100) if principal > 0 else 0
        
        # Calculate flexibility score (0-10)
        flexibility_score = 0.0
        if moratorium_months > 0:
            flexibility_score += min(moratorium_months / 12 * 3, 3)  # Up to 3 points for moratorium
        
        prepayment_penalty = extracted_data.get("prepayment_penalty", "")
        if prepayment_penalty and ("no penalty" in prepayment_penalty.lower() or "nil" in prepayment_penalty.lower()):
            flexibility_score += 3  # 3 points for no prepayment penalty
        
        if not extracted_data.get("collateral_details"):
            flexibility_score += 2  # 2 points for no collateral
        
        if not extracted_data.get("co_signer"):
            flexibility_score += 2  # 2 points for no co-signer
        
        loans.append(extracted_data)
        metrics.append({
            "loan_id": doc["name"],
            "total_cost_estimate": total_cost,
            "effective_interest_rate": effective_rate,
            "flexibility_score": flexibility_score,
            "monthly_emi": monthly_emi,
            "total_interest_payable": total_interest
        })
    
    # Find best options
    best_by_cost = min(metrics, key=lambda m: m["total_cost_estimate"])["loan_id"]
    best_by_flexibility = max(metrics, key=lambda m: m["flexibility_score"])["loan_id"]
    
    return {
        "loans": loans,
        "metrics": metrics,
        "best_by_cost": best_by_cost,
        "best_by_flexibility": best_by_flexibility,
        "comparison_notes": {
            "summary": f"Compared {len(loans)} loan options",
            "recommendation": "Review the comparison table and pros/cons below"
        }
    }


def display_comparison_results(comparison_result: Dict[str, Any], selected_docs: List[Dict[str, Any]]):
    """
    Display comparison results
    
    Args:
        comparison_result: Comparison result from API or local calculation
        selected_docs: List of selected document dictionaries
    """
    st.success("✓ Comparison complete!")
    
    st.markdown("---")
    st.markdown("### 🏆 Best Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        best_cost_id = comparison_result.get("best_by_cost", "")
        best_cost_doc = next((doc for doc in selected_docs if doc["name"] == best_cost_id), None)
        if best_cost_doc:
            st.success(f"**💰 Best by Cost**\n\n{best_cost_doc['name']}")
        else:
            st.info("Best by cost: Not determined")
    
    with col2:
        best_flex_id = comparison_result.get("best_by_flexibility", "")
        best_flex_doc = next((doc for doc in selected_docs if doc["name"] == best_flex_id), None)
        if best_flex_doc:
            st.success(f"**🔄 Best by Flexibility**\n\n{best_flex_doc['name']}")
        else:
            st.info("Best by flexibility: Not determined")
    
    st.markdown("---")
    
    # Comparison table
    st.markdown("### 📊 Comparison Table")
    
    comparison_data = []
    metrics_list = comparison_result.get("metrics", [])
    
    for doc, metrics in zip(selected_docs, metrics_list):
        extracted_data = doc.get("extracted_data", {})
        if "extracted_data_unmasked" in doc:
            extracted_data = doc["extracted_data_unmasked"]
        
        comparison_data.append({
            "Loan": doc["name"],
            "Bank": extracted_data.get("bank_name", "N/A"),
            "Type": extracted_data.get("loan_type", "N/A"),
            "Principal": f"${extracted_data.get('principal_amount', 0):,.2f}",
            "Interest Rate": f"{extracted_data.get('interest_rate', 0):.2f}%",
            "Tenure": f"{extracted_data.get('tenure_months', 0)} months",
            "Monthly EMI": f"${metrics.get('monthly_emi', 0):,.2f}",
            "Total Cost": f"${metrics.get('total_cost_estimate', 0):,.2f}",
            "Flexibility": f"{metrics.get('flexibility_score', 0):.1f}/10"
        })
    
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Pros and Cons for each loan
    st.markdown("### ⚖️ Pros and Cons")
    
    for doc, metrics in zip(selected_docs, metrics_list):
        extracted_data = doc.get("extracted_data", {})
        if "extracted_data_unmasked" in doc:
            extracted_data = doc["extracted_data_unmasked"]
        
        with st.expander(f"📄 {doc['name']} - {extracted_data.get('bank_name', 'Unknown')}"):
            pros, cons = generate_pros_cons(extracted_data, metrics, metrics_list)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### ✅ Pros")
                for pro in pros:
                    st.markdown(f"- {pro}")
            
            with col2:
                st.markdown("#### ❌ Cons")
                for con in cons:
                    st.markdown(f"- {con}")
    
    # Download comparison
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        # Download comparison as JSON
        comparison_json = json.dumps(comparison_result, indent=2)
        st.download_button(
            label="📥 Download Comparison (JSON)",
            data=comparison_json,
            file_name="loan_comparison.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        # Download comparison table as CSV
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Table (CSV)",
            data=csv_data,
            file_name="loan_comparison.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col3:
        if st.button("🔄 New Comparison", use_container_width=True):
            st.rerun()


def generate_pros_cons(
    extracted_data: Dict[str, Any],
    metrics: Dict[str, Any],
    all_metrics: List[Dict[str, Any]]
) -> tuple:
    """
    Generate pros and cons for a loan
    
    Args:
        extracted_data: Extracted loan data
        metrics: Metrics for this loan
        all_metrics: Metrics for all loans being compared
        
    Returns:
        Tuple of (pros list, cons list)
    """
    pros = []
    cons = []
    
    # Calculate averages
    avg_cost = sum(m.get("total_cost_estimate", 0) for m in all_metrics) / len(all_metrics)
    avg_rate = sum(m.get("effective_interest_rate", 0) for m in all_metrics) / len(all_metrics)
    avg_flexibility = sum(m.get("flexibility_score", 0) for m in all_metrics) / len(all_metrics)
    
    min_cost = min(m.get("total_cost_estimate", float('inf')) for m in all_metrics)
    max_cost = max(m.get("total_cost_estimate", 0) for m in all_metrics)
    min_rate = min(m.get("effective_interest_rate", float('inf')) for m in all_metrics)
    max_flexibility = max(m.get("flexibility_score", 0) for m in all_metrics)
    
    # Cost analysis
    total_cost = metrics.get("total_cost_estimate", 0)
    if total_cost == min_cost:
        pros.append("Lowest total cost among all options")
    elif total_cost <= avg_cost * 1.05:
        pros.append("Competitive total cost")
    elif total_cost >= max_cost * 0.95:
        cons.append("Highest total cost among options")
    
    # Interest rate analysis
    eff_rate = metrics.get("effective_interest_rate", 0)
    if eff_rate == min_rate:
        pros.append("Lowest effective interest rate")
    elif eff_rate <= avg_rate:
        pros.append("Below-average interest rate")
    else:
        cons.append("Above-average interest rate")
    
    # Flexibility analysis
    flex_score = metrics.get("flexibility_score", 0)
    if flex_score == max_flexibility:
        pros.append("Most flexible repayment terms")
    elif flex_score >= avg_flexibility:
        pros.append("Good repayment flexibility")
    else:
        cons.append("Limited repayment flexibility")
    
    # Moratorium period
    moratorium = extracted_data.get("moratorium_period_months", 0)
    if moratorium:
        if moratorium >= 12:
            pros.append(f"Generous moratorium period of {moratorium} months")
        elif moratorium >= 6:
            pros.append(f"Moratorium period of {moratorium} months available")
    else:
        cons.append("No moratorium period")
    
    # Prepayment penalty
    prepayment = extracted_data.get("prepayment_penalty", "")
    if prepayment:
        if "no penalty" in prepayment.lower() or "nil" in prepayment.lower():
            pros.append("No prepayment penalty")
        else:
            cons.append(f"Prepayment penalty: {prepayment}")
    
    # Processing fee
    processing_fee = extracted_data.get("processing_fee", 0)
    principal = extracted_data.get("principal_amount", 1)
    if processing_fee == 0:
        pros.append("No processing fee")
    elif principal > 0 and (processing_fee / principal) < 0.01:
        pros.append("Low processing fee")
    elif principal > 0 and (processing_fee / principal) > 0.03:
        cons.append("High processing fee")
    
    # Co-signer requirement
    if extracted_data.get("co_signer"):
        cons.append("Requires co-signer")
    else:
        pros.append("No co-signer required")
    
    # Collateral requirement
    if extracted_data.get("collateral_details"):
        cons.append(f"Requires collateral")
    else:
        pros.append("No collateral required")
    
    # Ensure we have at least some pros and cons
    if not pros:
        pros.append("Standard loan terms")
    if not cons:
        cons.append("No significant drawbacks identified")
    
    return pros, cons
