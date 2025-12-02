"""
Document Chunking Service
Chunks documents for vector storage while preserving context
"""

from typing import List, Dict, Any, Tuple
import re
import tiktoken
import logging

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Chunks documents intelligently for vector storage"""
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        model: str = "gpt-4"
    ):
        """
        Initialize chunker
        
        Args:
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
            model: Model name for token counting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            logger.warning(f"Model {model} not found, using cl100k_base encoding")
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def chunk_document(
        self,
        text: str,
        structured_data: Dict[str, Any],
        document_id: str
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Chunk document with metadata enrichment
        
        Args:
            text: Full document text
            structured_data: Lab3 extracted data for metadata
            document_id: Document identifier
            
        Returns:
            (chunks, metadatas) tuple
        """
        if not text or not text.strip():
            logger.warning(f"Empty text for document {document_id}")
            return [], []
        
        # Split into paragraphs first
        paragraphs = self._split_paragraphs(text)
        
        if not paragraphs:
            logger.warning(f"No paragraphs found in document {document_id}")
            return [text], [self._create_metadata(text, structured_data, 0)]
        
        # Create chunks with overlap
        chunks = []
        metadatas = []
        
        current_chunk = []
        current_tokens = 0
        chunk_index = 0
        
        for i, para in enumerate(paragraphs):
            para_tokens = len(self.encoding.encode(para))
            
            # If adding this paragraph exceeds chunk size and we have content
            if current_tokens + para_tokens > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(chunk_text)
                
                # Create metadata enriched with Lab3 data
                metadata = self._create_metadata(
                    chunk_text,
                    structured_data,
                    chunk_index
                )
                metadatas.append(metadata)
                
                # Start new chunk with overlap (keep last paragraph)
                overlap_paras = self._get_overlap_content(current_chunk)
                current_chunk = overlap_paras
                current_tokens = sum(
                    len(self.encoding.encode(p)) for p in current_chunk
                )
                chunk_index += 1
            
            current_chunk.append(para)
            current_tokens += para_tokens
        
        # Add final chunk if there's remaining content
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(chunk_text)
            metadatas.append(
                self._create_metadata(chunk_text, structured_data, chunk_index)
            )
        
        logger.info(f"Created {len(chunks)} chunks for document {document_id}")
        return chunks, metadatas
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs"""
        # Split on double newlines or section breaks
        paragraphs = re.split(r'\n\s*\n+', text)
        
        # Clean and filter
        cleaned = []
        for para in paragraphs:
            para = para.strip()
            if para and len(para) > 10:  # Minimum length filter
                cleaned.append(para)
        
        return cleaned
    
    def _get_overlap_content(self, paragraphs: List[str]) -> List[str]:
        """Get overlap content for next chunk"""
        if not paragraphs:
            return []
        
        # Calculate overlap in tokens
        overlap_paras = []
        overlap_tokens = 0
        
        # Work backwards from end of current chunk
        for para in reversed(paragraphs):
            para_tokens = len(self.encoding.encode(para))
            if overlap_tokens + para_tokens <= self.chunk_overlap:
                overlap_paras.insert(0, para)
                overlap_tokens += para_tokens
            else:
                break
        
        return overlap_paras
    
    def _create_metadata(
        self,
        chunk_text: str,
        structured_data: Dict[str, Any],
        chunk_index: int
    ) -> Dict[str, Any]:
        """
        Create enriched metadata for chunk
        
        Args:
            chunk_text: Text of the chunk
            structured_data: Lab3 extracted structured data
            chunk_index: Index of this chunk in document
            
        Returns:
            Metadata dictionary
        """
        # Detect section type based on content
        section_type = self._detect_section_type(chunk_text)
        
        # Extract page number if present (basic heuristic)
        page_number = self._extract_page_number(chunk_text, chunk_index)
        
        # Build metadata with Lab3 integration
        metadata = {
            'chunk_index': chunk_index,
            'section_type': section_type,
            'token_count': len(self.encoding.encode(chunk_text)),
            'page_number': page_number,
        }
        
        # Add Lab3 structured data
        if structured_data:
            # Add key loan details
            if 'bank_name' in structured_data:
                metadata['bank_name'] = structured_data['bank_name']
            
            if 'loan_type' in structured_data:
                metadata['loan_type'] = structured_data['loan_type']
            
            if 'principal_amount' in structured_data:
                metadata['principal'] = structured_data['principal_amount']
            
            if 'interest_rate' in structured_data:
                metadata['interest_rate'] = structured_data['interest_rate']
            
            if 'tenure_months' in structured_data:
                metadata['tenure_months'] = structured_data['tenure_months']
            
            # Add extraction confidence
            if 'accuracy_metrics' in structured_data:
                accuracy = structured_data['accuracy_metrics']
                if isinstance(accuracy, dict):
                    metadata['extraction_confidence'] = accuracy.get(
                        'overall_accuracy', 0.0
                    )
                else:
                    metadata['extraction_confidence'] = accuracy
        
        return metadata
    
    @staticmethod
    def _detect_section_type(text: str) -> str:
        """
        Detect section type from content
        
        Args:
            text: Chunk text
            
        Returns:
            Section type identifier
        """
        lower_text = text.lower()
        
        # Define section keywords
        section_keywords = {
            'payment_terms': ['payment', 'emi', 'monthly payment', 'installment', 'schedule'],
            'interest_terms': ['interest', 'rate', 'apr', 'annual percentage'],
            'fees': ['fee', 'charge', 'cost', 'processing fee', 'documentation'],
            'penalties': ['penalty', 'default', 'late payment', 'late fee'],
            'prepayment': ['prepayment', 'early payment', 'foreclosure', 'pre-closure'],
            'collateral': ['collateral', 'security', 'mortgage', 'guarantee'],
            'eligibility': ['eligibility', 'qualification', 'requirement', 'criteria'],
            'loan_details': ['principal', 'loan amount', 'disbursement', 'tenure'],
            'terms_conditions': ['terms', 'conditions', 'agreement', 'covenant']
        }
        
        # Count matches for each section type
        matches = {}
        for section, keywords in section_keywords.items():
            count = sum(1 for kw in keywords if kw in lower_text)
            if count > 0:
                matches[section] = count
        
        # Return section with most matches
        if matches:
            return max(matches, key=matches.get)
        
        return 'general'
    
    @staticmethod
    def _extract_page_number(text: str, chunk_index: int) -> int:
        """
        Extract page number from text (if present)
        
        Args:
            text: Chunk text
            chunk_index: Index of chunk
            
        Returns:
            Page number (estimated if not found)
        """
        # Look for page number patterns
        patterns = [
            r'page\s+(\d+)',
            r'pg\.\s*(\d+)',
            r'p\.\s*(\d+)',
            r'^(\d+)$'  # Standalone number
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        # Fallback: estimate based on chunk index
        # Assume ~3 chunks per page on average
        return (chunk_index // 3) + 1


# Utility function for easy usage
def chunk_document(
    text: str,
    structured_data: Dict[str, Any] = None,
    document_id: str = "unknown",
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Quick function to chunk a document
    
    Args:
        text: Document text
        structured_data: Optional structured data from Lab3
        document_id: Document identifier
        chunk_size: Target chunk size in tokens
        chunk_overlap: Overlap between chunks
        
    Returns:
        (chunks, metadatas) tuple
    """
    chunker = DocumentChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return chunker.chunk_document(
        text=text,
        structured_data=structured_data or {},
        document_id=document_id
    )
