"""
Test script for Vector Store
Verifies ChromaDB connection and basic operations
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.services.vector_store import VectorStoreManager
from src.services.chunking import DocumentChunker

# Load environment
load_dotenv(project_root / '.env')


def test_connection():
    """Test ChromaDB connection"""
    print("\n" + "="*60)
    print("Test 1: ChromaDB Connection")
    print("="*60)
    
    try:
        vector_store = VectorStoreManager(
            chroma_host=os.getenv('CHROMADB_HOST', 'localhost'),
            chroma_port=int(os.getenv('CHROMADB_PORT', '8001')),
            use_openai=False  # Use local model for testing
        )
        
        stats = vector_store.get_stats()
        print(f"✅ Connection successful!")
        print(f"   Status: {stats['status']}")
        print(f"   Total chunks: {stats.get('total_chunks', 0)}")
        print(f"   Provider: {stats.get('provider', 'unknown')}")
        return vector_store
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None


def test_chunking():
    """Test document chunking"""
    print("\n" + "="*60)
    print("Test 2: Document Chunking")
    print("="*60)
    
    try:
        # Sample loan document text
        sample_text = """
Student Loan Agreement

Loan Details:
Principal Amount: $10,000
Interest Rate: 5.5% per annum
Tenure: 60 months
Monthly Payment: $191.23

Payment Terms:
The borrower agrees to repay the loan in equal monthly installments.
Payments are due on the 1st of each month.
Late payments will incur a penalty of $25.

Prepayment Policy:
The borrower may prepay the loan at any time without penalty.
Prepaid amounts will be applied to the principal balance.

Default Provisions:
In case of default, the entire outstanding balance becomes due immediately.
The lender may pursue legal action for collection.
        """
        
        structured_data = {
            'bank_name': 'Test Bank',
            'loan_type': 'education',
            'principal_amount': 10000,
            'interest_rate': 5.5,
            'tenure_months': 60,
            'accuracy_metrics': {'overall_accuracy': 0.95}
        }
        
        chunker = DocumentChunker(chunk_size=200, chunk_overlap=50)
        chunks, metadatas = chunker.chunk_document(
            text=sample_text,
            structured_data=structured_data,
            document_id='test-doc-001'
        )
        
        print(f"✅ Chunking successful!")
        print(f"   Created {len(chunks)} chunks")
        print(f"\n   Sample chunk 1:")
        print(f"   Text: {chunks[0][:100]}...")
        print(f"   Metadata: {metadatas[0]}")
        
        return chunks, metadatas
        
    except Exception as e:
        print(f"❌ Chunking failed: {e}")
        return None, None


def test_indexing(vector_store, chunks, metadatas):
    """Test adding chunks to vector store"""
    print("\n" + "="*60)
    print("Test 3: Vector Indexing")
    print("="*60)
    
    if not vector_store or not chunks:
        print("⏭️  Skipping (prerequisites failed)")
        return False
    
    try:
        chunk_ids = vector_store.add_document_chunks(
            document_id='test-doc-001',
            chunks=chunks,
            metadatas=metadatas
        )
        
        print(f"✅ Indexing successful!")
        print(f"   Indexed {len(chunk_ids)} chunks")
        print(f"   Sample chunk ID: {chunk_ids[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Indexing failed: {e}")
        return False


def test_search(vector_store):
    """Test semantic search"""
    print("\n" + "="*60)
    print("Test 4: Semantic Search")
    print("="*60)
    
    if not vector_store:
        print("⏭️  Skipping (vector store not available)")
        return False
    
    try:
        # Test queries
        queries = [
            "What is the prepayment policy?",
            "What happens if I miss a payment?",
            "What is the interest rate?"
        ]
        
        for query in queries:
            print(f"\n   Query: {query}")
            results = vector_store.search(
                query=query,
                n_results=2,
                document_filter='test-doc-001'
            )
            
            if results['chunks']:
                print(f"   ✅ Found {len(results['chunks'])} results")
                print(f"   Top result: {results['chunks'][0][:80]}...")
                print(f"   Distance: {results['distances'][0]:.4f}")
            else:
                print(f"   ⚠️  No results found")
        
        print(f"\n✅ Search test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return False


def test_cleanup(vector_store):
    """Clean up test data"""
    print("\n" + "="*60)
    print("Test 5: Cleanup")
    print("="*60)
    
    if not vector_store:
        print("⏭️  Skipping (vector store not available)")
        return
    
    try:
        deleted = vector_store.delete_document('test-doc-001')
        print(f"✅ Cleanup successful!")
        print(f"   Deleted {deleted} chunks")
        
    except Exception as e:
        print(f"⚠️  Cleanup failed: {e}")


def main():
    """Run all tests"""
    print("="*60)
    print("Vector Store Test Suite")
    print("="*60)
    print("\nThis will test:")
    print("  1. ChromaDB connection")
    print("  2. Document chunking")
    print("  3. Vector indexing")
    print("  4. Semantic search")
    print("  5. Data cleanup")
    
    # Test 1: Connection
    vector_store = test_connection()
    
    # Test 2: Chunking
    chunks, metadatas = test_chunking()
    
    # Test 3: Indexing
    if chunks and metadatas:
        indexing_ok = test_indexing(vector_store, chunks, metadatas)
    else:
        indexing_ok = False
    
    # Test 4: Search
    if indexing_ok:
        test_search(vector_store)
    
    # Test 5: Cleanup
    test_cleanup(vector_store)
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    if vector_store and chunks and indexing_ok:
        print("✅ All tests passed!")
        print("\n🎉 Vector store is working correctly!")
        print("\nYou can now:")
        print("  1. Start processing real documents")
        print("  2. Test the chat interface")
        print("  3. Build hybrid queries")
    else:
        print("⚠️  Some tests failed")
        print("\nPlease check:")
        print("  - ChromaDB is running (docker-compose up chromadb)")
        print("  - Dependencies are installed (pip install -r requirements.txt)")
        print("  - Configuration in .env is correct")
    
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
