"""
Vector Store Manager for Semantic Search
Integrates ChromaDB with Lab3 extraction metadata
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import openai
from sentence_transformers import SentenceTransformer
import logging
import uuid
import os

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages vector storage and retrieval for document chunks"""
    
    def __init__(
        self,
        chroma_host: str = None,
        chroma_port: int = None,
        embedding_model: str = "text-embedding-3-small",
        use_openai: bool = True
    ):
        """
        Initialize vector store
        
        Args:
            chroma_host: ChromaDB host (default: localhost)
            chroma_port: ChromaDB port (default: 8001)
            embedding_model: Model name for embeddings
            use_openai: Use OpenAI embeddings (faster, better quality)
        """
        self.use_openai = use_openai
        self.embedding_model = embedding_model
        
        # Use localhost by default for host machine access
        if chroma_host is None:
            chroma_host = "localhost"
        if chroma_port is None:
            chroma_port = 8001
        
        try:
            # Initialize ChromaDB client (compatible with v2 API)
            self.client = chromadb.HttpClient(
                host=chroma_host,
                port=chroma_port
            )
            
            # Test connection
            self.client.heartbeat()
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="loan_documents",
                metadata={
                    "description": "Student loan document chunks with Lab3 metadata",
                    "embedding_model": embedding_model
                }
            )
            
            logger.info(
                f"Vector store initialized: {self.collection.count()} chunks loaded"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            logger.warning("Vector store will operate in degraded mode")
            self.client = None
            self.collection = None
        
        # Initialize embedding model
        if not use_openai:
            logger.info("Loading sentence transformer model...")
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            self.sentence_model = None
            # Set OpenAI API key
            openai.api_key = os.getenv('OPENAI_API_KEY')
    
    def add_document_chunks(
        self,
        document_id: str,
        chunks: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Add document chunks to vector store
        
        Args:
            document_id: Document identifier
            chunks: List of text chunks
            metadatas: Metadata for each chunk (from Lab3 extraction)
            
        Returns:
            List of chunk IDs
            
        Raises:
            RuntimeError: If vector store not initialized
        """
        if not self.collection:
            raise RuntimeError("Vector store not initialized")
        
        if len(chunks) != len(metadatas):
            raise ValueError("Chunks and metadatas must have same length")
        
        # Generate unique IDs
        chunk_ids = [str(uuid.uuid4()) for _ in chunks]
        
        # Enrich metadata with document_id
        for meta in metadatas:
            meta['document_id'] = document_id
            # Convert numeric values to strings for ChromaDB
            for key, value in meta.items():
                if isinstance(value, (int, float)):
                    meta[key] = str(value)
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = self._generate_embeddings(chunks)
        
        # Add to ChromaDB
        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=chunk_ids
        )
        
        logger.info(f"Added {len(chunks)} chunks for document {document_id}")
        return chunk_ids
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        document_filter: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search for relevant chunks using semantic similarity
        
        Args:
            query: Search query
            n_results: Number of results to return
            document_filter: Filter by document_id
            metadata_filter: Additional metadata filters
            
        Returns:
            Dict with 'chunks', 'metadatas', 'distances', 'ids'
            
        Raises:
            RuntimeError: If vector store not initialized
        """
        if not self.collection:
            raise RuntimeError("Vector store not initialized")
        
        # Build where filter
        where_filter = {}
        if document_filter:
            where_filter['document_id'] = document_filter
        if metadata_filter:
            # Convert numeric filters to strings
            for key, value in metadata_filter.items():
                if isinstance(value, (int, float)):
                    where_filter[key] = str(value)
                else:
                    where_filter[key] = value
        
        # Generate query embedding
        logger.info(f"Searching for: {query[:100]}...")
        query_embedding = self._generate_embeddings([query])[0]
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter if where_filter else None
        )
        
        logger.info(f"Found {len(results['documents'][0])} results")
        
        return {
            'chunks': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [],
            'distances': results['distances'][0] if results['distances'] else [],
            'ids': results['ids'][0] if results['ids'] else []
        }
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        if self.use_openai:
            try:
                response = openai.embeddings.create(
                    model=self.embedding_model,
                    input=texts
                )
                return [item.embedding for item in response.data]
            except Exception as e:
                logger.error(f"OpenAI embedding failed: {e}")
                logger.info("Falling back to sentence transformers")
                # Fallback to local model
                if not self.sentence_model:
                    self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                return self.sentence_model.encode(texts).tolist()
        else:
            return self.sentence_model.encode(texts).tolist()
    
    def delete_document(self, document_id: str) -> int:
        """
        Delete all chunks for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            Number of chunks deleted
            
        Raises:
            RuntimeError: If vector store not initialized
        """
        if not self.collection:
            raise RuntimeError("Vector store not initialized")
        
        # Get all chunks for document
        results = self.collection.get(
            where={"document_id": document_id}
        )
        
        if results['ids']:
            self.collection.delete(ids=results['ids'])
            logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
            return len(results['ids'])
        
        logger.info(f"No chunks found for document {document_id}")
        return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        if not self.collection:
            return {'status': 'not_initialized', 'count': 0}
        
        try:
            count = self.collection.count()
            return {
                'status': 'active',
                'total_chunks': count,
                'embedding_model': self.embedding_model,
                'provider': 'openai' if self.use_openai else 'sentence-transformers'
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def reset(self) -> None:
        """Reset vector store (delete all data) - USE WITH CAUTION"""
        if not self.client:
            raise RuntimeError("Vector store not initialized")
        
        logger.warning("Resetting vector store - all data will be deleted!")
        self.client.delete_collection(name="loan_documents")
        self.collection = self.client.create_collection(
            name="loan_documents",
            metadata={
                "description": "Student loan document chunks with Lab3 metadata",
                "embedding_model": self.embedding_model
            }
        )
        logger.info("Vector store reset complete")


# Create singleton instance
_vector_store = None

def get_vector_store() -> VectorStoreManager:
    """Get or create vector store singleton"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreManager(
            chroma_host=os.getenv('CHROMADB_HOST', 'localhost'),
            chroma_port=int(os.getenv('CHROMADB_PORT', '8001')),
            embedding_model=os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small'),
            use_openai=True
        )
    return _vector_store
