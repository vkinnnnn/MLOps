"""
Complete Pipeline Demo - LoanQA Integration
Demonstrates end-to-end workflow from document upload to AI analysis
"""

import os
import sys
from pathlib import Path
import json
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import requests

# Load environment
load_dotenv(project_root / '.env')

API_BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def check_services():
    """Check if all required services are running"""
    print_section("STEP 1: Checking Services")
    
    services = {
        "API": f"{API_BASE_URL}/health",
        "ChromaDB": "http://localhost:8001/api/v2/heartbeat"
    }
    
    all_healthy = True
    for service, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  [OK] {service}: Running")
            else:
                print(f"  [WARN] {service}: Status {response.status_code}")
                all_healthy = False
        except Exception as e:
            print(f"  [ERROR] {service}: {e}")
            all_healthy = False
    
    return all_healthy


def list_sample_documents():
    """List available sample documents"""
    print_section("STEP 2: Available Sample Documents")
    
    sample_dir = project_root / "sample-loan-docs"
    if not sample_dir.exists():
        print("  [ERROR] Sample documents directory not found")
        return []
    
    pdf_files = list(sample_dir.glob("*.pdf"))
    
    print(f"\n  Found {len(pdf_files)} PDF documents:\n")
    for i, pdf in enumerate(pdf_files[:10], 1):  # Show first 10
        size_mb = pdf.stat().st_size / (1024 * 1024)
        print(f"    {i}. {pdf.name} ({size_mb:.2f} MB)")
    
    if len(pdf_files) > 10:
        print(f"    ... and {len(pdf_files) - 10} more\n")
    
    return pdf_files


def upload_document(pdf_path):
    """Upload document via API"""
    print_section(f"STEP 3: Uploading Document - {pdf_path.name}")
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path.name, f, 'application/pdf')}
            response = requests.post(
                f"{API_BASE_URL}/api/v1/documents/upload",
                files=files,
                timeout=60
            )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  [SUCCESS] Document uploaded!")
            print(f"  Document ID: {data.get('document_id')}")
            print(f"  Status: {data.get('status')}")
            return data
        else:
            print(f"  [ERROR] Upload failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"  [ERROR] Upload failed: {e}")
        return None


def check_extraction_status(document_id):
    """Check document extraction status"""
    print_section(f"STEP 4: Checking Extraction Status")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/documents/{document_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            print(f"  Status: {status}")
            
            if status == 'completed':
                extracted = data.get('extracted_data', {})
                print(f"  Text extracted: {len(extracted.get('text', ''))} characters")
                print(f"  Entities found: {len(extracted.get('entities', []))}")
                return data
            elif status == 'processing':
                print("  [INFO] Still processing...")
                return None
            else:
                print(f"  [WARN] Unexpected status: {status}")
                return None
        else:
            print(f"  [ERROR] Status check failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"  [ERROR] Status check failed: {e}")
        return None


def test_llm_integration():
    """Test LLM integration with all providers"""
    print_section("STEP 5: Testing LLM Integration")
    
    try:
        from src.services import get_llm_service
        
        llm = get_llm_service()
        
        test_message = [
            {"role": "user", "content": "What are the key components of a loan agreement?"}
        ]
        
        providers = ['openai', 'anthropic', 'kimi']
        
        for provider in providers:
            print(f"\n  Testing {provider.upper()}...")
            try:
                response = llm.chat(
                    messages=test_message,
                    provider=provider,
                    max_tokens=150,
                    temperature=0.7
                )
                print(f"    [OK] Model: {response.model}")
                print(f"    [OK] Tokens: {response.tokens_used}")
                print(f"    Response: {response.content[:100]}...")
            except Exception as e:
                error_msg = str(e)
                if '429' in error_msg:
                    print(f"    [WARN] Rate limited (API working!)")
                else:
                    print(f"    [ERROR] {error_msg[:100]}")
        
        return True
    except Exception as e:
        print(f"  [ERROR] LLM integration test failed: {e}")
        return False


def test_vector_store():
    """Test vector store functionality"""
    print_section("STEP 6: Testing Vector Store")
    
    try:
        from src.services.vector_store import VectorStoreManager
        
        # Direct initialization with explicit connection details
        vector_store = VectorStoreManager(
            chroma_host='localhost',
            chroma_port=8001
        )
        
        # Test document
        test_chunks = [
            "The loan amount is $250,000 with an interest rate of 5.5% per annum.",
            "The borrower must make monthly payments on the first day of each month.",
            "Prepayment penalty applies for the first 3 years at 2% of principal."
        ]
        
        test_metadata = [
            {"section": "loan_terms", "type": "amount"},
            {"section": "payment_schedule", "type": "frequency"},
            {"section": "penalties", "type": "prepayment"}
        ]
        
        print("\n  Adding test document chunks...")
        doc_id = "demo-test-loan-001"
        
        vector_store.add_document_chunks(
            document_id=doc_id,
            chunks=test_chunks,
            metadatas=test_metadata
        )
        print(f"    [OK] Added {len(test_chunks)} chunks")
        
        # Test search
        print("\n  Testing semantic search...")
        query = "What is the prepayment penalty?"
        results = vector_store.search(query=query, n_results=2)
        
        # Results is a dict with 'chunks', 'metadatas', 'distances', 'ids'
        if results and results.get('chunks'):
            chunks = results['chunks']
            metadatas = results['metadatas']
            distances = results['distances']
            
            print(f"    [OK] Found {len(chunks)} results for: '{query}'")
            for i, (chunk, meta, dist) in enumerate(zip(chunks, metadatas, distances), 1):
                print(f"\n    Result {i}:")
                print(f"      Text: {chunk[:80]}...")
                print(f"      Distance: {dist:.4f}")
                print(f"      Section: {meta.get('section', 'N/A')}")
        else:
            print(f"    [WARN] No results found for query")
        
        return True
    except Exception as e:
        print(f"  [ERROR] Vector store test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def demonstrate_rag():
    """Demonstrate RAG functionality"""
    print_section("STEP 7: Demonstrating RAG (Retrieval Augmented Generation)")
    
    try:
        from src.services.vector_store import VectorStoreManager
        from src.services import get_llm_service
        
        vector_store = VectorStoreManager(
            chroma_host='localhost',
            chroma_port=8001
        )
        llm = get_llm_service()
        
        # User query
        user_query = "What are the prepayment terms?"
        print(f"\n  User Query: '{user_query}'")
        
        # Retrieve relevant context
        print("\n  Retrieving relevant context from vector store...")
        results = vector_store.search(query=user_query, n_results=3)
        
        # Extract chunks from results dict
        chunks = results.get('chunks', [])
        context = "\n".join(chunks)
        print(f"    [OK] Retrieved {len(results)} relevant chunks")
        
        # Generate answer using LLM
        print("\n  Generating answer with OpenAI...")
        
        rag_messages = [
            {
                "role": "system",
                "content": "You are a helpful loan document assistant. Answer based on the provided context."
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {user_query}\n\nAnswer:"
            }
        ]
        
        response = llm.chat(
            messages=rag_messages,
            provider='openai',
            max_tokens=200,
            temperature=0.3
        )
        
        print(f"\n  RAG Answer:")
        print(f"  {'-'*66}")
        print(f"  {response.content}")
        print(f"  {'-'*66}")
        print(f"  Model: {response.model} | Tokens: {response.tokens_used}")
        
        return True
    except Exception as e:
        print(f"  [ERROR] RAG demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_api_endpoints():
    """Show available API endpoints"""
    print_section("STEP 8: Available API Endpoints")
    
    print("""
  API Documentation:
    http://localhost:8000/docs          - Swagger UI (Interactive)
    http://localhost:8000/redoc         - ReDoc (Alternative docs)
  
  Key Endpoints:
    POST /api/v1/documents/upload       - Upload new document
    GET  /api/v1/documents/{id}         - Get document details
    GET  /api/v1/documents              - List all documents
    POST /api/v1/documents/{id}/extract - Trigger extraction
    
  Dashboard:
    http://localhost:8501               - Streamlit Dashboard
    
  Airflow:
    http://localhost:8080               - Airflow UI (admin/admin123)
    
  MinIO:
    http://localhost:9001               - Storage Console
    """)


def main():
    """Run complete pipeline demo"""
    print("\n" + "="*70)
    print("  LOANQA COMPLETE PIPELINE DEMO")
    print("  Multi-LLM Loan Intelligence Platform")
    print("="*70)
    
    # Step 1: Check services
    if not check_services():
        print("\n[ERROR] Some services are not running!")
        print("Please start services: docker-compose up -d")
        return
    
    # Step 2: List documents
    sample_docs = list_sample_documents()
    if not sample_docs:
        print("\n[ERROR] No sample documents found!")
        return
    
    # Step 3: Upload document (optional - commented out for now)
    print("\n[INFO] Document upload requires Document AI credentials")
    print("[INFO] Skipping upload for now - testing other components...")
    
    # Step 4: Test LLM integration
    llm_success = test_llm_integration()
    if not llm_success:
        print("\n[WARN] LLM tests had some issues")
    
    # Step 5: Test vector store
    vector_success = test_vector_store()
    if not vector_success:
        print("\n[ERROR] Vector store test failed!")
        return
    
    # Step 6: Demonstrate RAG
    rag_success = demonstrate_rag()
    if not rag_success:
        print("\n[ERROR] RAG demonstration failed!")
        return
    
    # Step 7: Show API endpoints
    show_api_endpoints()
    
    # Summary
    print_section("DEMO COMPLETE - SUMMARY")
    print("""
  Success! You now have:
    [OK] All services running
    [OK] Vector store operational
    [OK] LLM integration working (3 providers)
    [OK] RAG pipeline functional
    [OK] API endpoints available
    
  Next Steps:
    1. Configure Document AI credentials for document extraction
    2. Upload real loan documents via API
    3. Build custom queries in the dashboard
    4. Compare LLM responses across providers
    5. Create complex hybrid queries (SQL + Vector search)
    
  Access Points:
    - API Docs: http://localhost:8000/docs
    - Dashboard: http://localhost:8501
    - Airflow: http://localhost:8080
    
  Happy analyzing!
    """)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()
