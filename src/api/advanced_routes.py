"""
Advanced Feature API Routes
Provides REST endpoints for translation, chatbot, comparison, and education services
Following KIRO Global Steering Guidelines
"""

from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator
import logging

from src.api.services.translation_service import translation_service
from src.api.services.rag_chatbot_service import financial_chatbot
from src.api.services.comparison_engine import comparison_engine
from src.api.services.financial_education import financial_education

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advanced", tags=["Advanced Features"])


# ========================================================================
# Pydantic Models for Request/Response Validation
# ========================================================================

class TranslationRequest(BaseModel):
    """Request model for translation"""
    text: str = Field(..., min_length=1, max_length=50000, description="Text to translate")
    target_lang: str = Field(..., min_length=2, max_length=10, description="Target language code")
    source_lang: str = Field("auto", description="Source language (auto-detect by default)")
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate text is not empty"""
        if not v.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        return v.strip()


class DocumentTranslationRequest(BaseModel):
    """Request model for document translation"""
    extraction_result: Dict[str, Any] = Field(..., description="Lab3 extraction result")
    target_lang: str = Field(..., min_length=2, max_length=10, description="Target language code")


class ChatbotRequest(BaseModel):
    """Request model for chatbot queries"""
    question: str = Field(..., min_length=1, max_length=1000, description="User's question")
    document_id: str = Field(..., min_length=1, description="Document identifier")
    structured_data: Optional[Dict[str, Any]] = Field(None, description="Lab3 extracted structured data")
    use_memory: bool = Field(True, description="Use conversation history")
    
    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Validate question is not empty"""
        if not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()


class ComparisonRequest(BaseModel):
    """Request model for loan comparison"""
    loans: List[Dict[str, Any]] = Field(..., min_items=1, max_items=10, description="List of loan documents")
    
    @field_validator('loans')
    @classmethod
    def validate_loans(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate loans list"""
        if len(v) < 1:
            raise ValueError("At least one loan is required")
        if len(v) > 10:
            raise ValueError("Maximum 10 loans can be compared at once")
        return v


class TermExplanationRequest(BaseModel):
    """Request model for term explanation"""
    term: str = Field(..., min_length=1, max_length=100, description="Financial term to explain")
    language: str = Field("en", min_length=2, max_length=10, description="Language code")
    include_related: bool = Field(False, description="Include related terms")


class ScenarioRequest(BaseModel):
    """Request model for scenario simulation"""
    scenario_type: str = Field(..., description="Type of scenario (extra_payment, tenure_comparison)")
    params: Dict[str, Any] = Field(..., description="Scenario parameters")
    
    @field_validator('scenario_type')
    @classmethod
    def validate_scenario_type(cls, v: str) -> str:
        """Validate scenario type"""
        valid_types = ['extra_payment', 'tenure_comparison']
        if v not in valid_types:
            raise ValueError(f"Scenario type must be one of: {', '.join(valid_types)}")
        return v


class BestPracticesRequest(BaseModel):
    """Request model for best practices"""
    role: Optional[str] = Field(None, description="User role (student, parent)")
    category: Optional[str] = Field(None, description="Practice category")
    importance: Optional[str] = Field(None, description="Importance level (high, medium, low)")


# ========================================================================
# Translation Service Endpoints
# ========================================================================

@router.post("/translate/text", status_code=status.HTTP_200_OK)
async def translate_text(request: TranslationRequest) -> Dict[str, Any]:
    """
    Translate text to target language
    
    Args:
        request: Translation request with text and target language
        
    Returns:
        Translation result with source language detection
        
    Raises:
        HTTPException: If translation fails
    """
    try:
        logger.info(f"Translating text to {request.target_lang}")
        
        result = translation_service.translate_text(
            text=request.text,
            target_lang=request.target_lang,
            source_lang=request.source_lang
        )
        
        return {
            "success": True,
            "translation": result
        }
        
    except Exception as e:
        logger.error(f"Translation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )


@router.post("/translate/document", status_code=status.HTTP_200_OK)
async def translate_document(request: DocumentTranslationRequest) -> Dict[str, Any]:
    """
    Translate extracted document data
    
    Args:
        request: Document translation request
        
    Returns:
        Translated document data
        
    Raises:
        HTTPException: If translation fails
    """
    try:
        logger.info(f"Translating document to {request.target_lang}")
        
        translated_result = translation_service.translate_document_data(
            extraction_result=request.extraction_result,
            target_lang=request.target_lang
        )
        
        return {
            "success": True,
            "translated_document": translated_result
        }
        
    except Exception as e:
        logger.error(f"Document translation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document translation failed: {str(e)}"
        )


@router.get("/translate/languages", status_code=status.HTTP_200_OK)
async def get_supported_languages() -> Dict[str, Any]:
    """
    Get list of supported languages
    
    Returns:
        List of supported language codes with names
    """
    try:
        languages = translation_service.get_supported_languages()
        
        return {
            "success": True,
            "languages": languages
        }
        
    except Exception as e:
        logger.error(f"Failed to get languages: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get languages: {str(e)}"
        )


# ========================================================================
# RAG Chatbot Endpoints
# ========================================================================

@router.post("/chatbot/ask", status_code=status.HTTP_200_OK)
async def ask_chatbot(request: ChatbotRequest) -> Dict[str, Any]:
    """
    Ask chatbot a question about loan document
    
    Args:
        request: Chatbot request with question and document context
        
    Returns:
        Answer with sources and confidence
        
    Raises:
        HTTPException: If query processing fails
    """
    try:
        logger.info(f"Processing chatbot question for document {request.document_id}")
        
        response = financial_chatbot.ask(
            question=request.question,
            document_id=request.document_id,
            structured_data=request.structured_data,
            use_memory=request.use_memory
        )
        
        return {
            "success": True,
            "response": response.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Chatbot query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chatbot query failed: {str(e)}"
        )


@router.get("/chatbot/history", status_code=status.HTTP_200_OK)
async def get_conversation_history() -> Dict[str, Any]:
    """
    Get conversation history
    
    Returns:
        List of conversation messages
    """
    try:
        history = financial_chatbot.get_conversation_history()
        
        return {
            "success": True,
            "history": history
        }
        
    except Exception as e:
        logger.error(f"Failed to get history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation history: {str(e)}"
        )


@router.post("/chatbot/clear", status_code=status.HTTP_200_OK)
async def clear_conversation() -> Dict[str, Any]:
    """
    Clear conversation history
    
    Returns:
        Success confirmation
    """
    try:
        financial_chatbot.clear_conversation()
        
        return {
            "success": True,
            "message": "Conversation history cleared"
        }
        
    except Exception as e:
        logger.error(f"Failed to clear history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear conversation: {str(e)}"
        )


# ========================================================================
# Comparison Engine Endpoints
# ========================================================================

@router.post("/compare/loans", status_code=status.HTTP_200_OK)
async def compare_loans(request: ComparisonRequest) -> Dict[str, Any]:
    """
    Compare multiple loan documents
    
    Args:
        request: Comparison request with list of loans
        
    Returns:
        Comprehensive comparison with recommendations
        
    Raises:
        HTTPException: If comparison fails
    """
    try:
        logger.info(f"Comparing {len(request.loans)} loans")
        
        result = comparison_engine.compare_loans(request.loans)
        
        return {
            "success": True,
            "comparison": result.to_dict()
        }
        
    except ValueError as e:
        logger.warning(f"Invalid comparison request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Comparison failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed: {str(e)}"
        )


# ========================================================================
# Financial Education Endpoints
# ========================================================================

@router.post("/education/explain-term", status_code=status.HTTP_200_OK)
async def explain_term(request: TermExplanationRequest) -> Dict[str, Any]:
    """
    Explain a financial term
    
    Args:
        request: Term explanation request
        
    Returns:
        Term explanation with examples
        
    Raises:
        HTTPException: If explanation fails
    """
    try:
        logger.info(f"Explaining term: {request.term}")
        
        result = financial_education.explain_term(
            term=request.term,
            language=request.language,
            include_related=request.include_related
        )
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"Term explanation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to explain term: {str(e)}"
        )


@router.get("/education/glossary", status_code=status.HTTP_200_OK)
async def get_glossary(
    category: Optional[str] = None,
    search: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get financial glossary
    
    Args:
        category: Optional category filter
        search: Optional search query
        
    Returns:
        List of financial terms
    """
    try:
        if search:
            terms = financial_education.search_glossary(search)
        else:
            terms = financial_education.get_all_terms(category=category)
        
        return {
            "success": True,
            "terms": terms,
            "count": len(terms)
        }
        
    except Exception as e:
        logger.error(f"Failed to get glossary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get glossary: {str(e)}"
        )


@router.post("/education/simulate", status_code=status.HTTP_200_OK)
async def simulate_scenario(request: ScenarioRequest) -> Dict[str, Any]:
    """
    Simulate financial scenario
    
    Args:
        request: Scenario simulation request
        
    Returns:
        Scenario results with analysis
        
    Raises:
        HTTPException: If simulation fails
    """
    try:
        logger.info(f"Simulating scenario: {request.scenario_type}")
        
        result = financial_education.simulate_scenario(
            scenario_type=request.scenario_type,
            params=request.params
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Scenario simulation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scenario simulation failed: {str(e)}"
        )


@router.post("/education/best-practices", status_code=status.HTTP_200_OK)
async def get_best_practices(request: BestPracticesRequest) -> Dict[str, Any]:
    """
    Get financial best practices
    
    Args:
        request: Best practices request with filters
        
    Returns:
        List of best practice recommendations
    """
    try:
        user_profile = {}
        if request.role:
            user_profile['role'] = request.role
        if request.category:
            user_profile['category'] = request.category
        if request.importance:
            user_profile['importance'] = request.importance
        
        practices = financial_education.get_best_practices(
            user_profile=user_profile if user_profile else None
        )
        
        return {
            "success": True,
            "practices": practices,
            "count": len(practices)
        }
        
    except Exception as e:
        logger.error(f"Failed to get best practices: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get best practices: {str(e)}"
        )


@router.get("/education/learning-path/{user_type}", status_code=status.HTTP_200_OK)
async def get_learning_path(user_type: str) -> Dict[str, Any]:
    """
    Get learning path for user type
    
    Args:
        user_type: Type of user (student or parent)
        
    Returns:
        Structured learning path with modules
        
    Raises:
        HTTPException: If invalid user type
    """
    try:
        if user_type not in ['student', 'parent']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User type must be 'student' or 'parent'"
            )
        
        path = financial_education.get_learning_path(user_type=user_type)
        
        return {
            "success": True,
            "learning_path": path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get learning path: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get learning path: {str(e)}"
        )


# ========================================================================
# Health Check Endpoint
# ========================================================================

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Health check for advanced services
    
    Returns:
        Health status of all services
    """
    return {
        "status": "healthy",
        "services": {
            "translation": "operational",
            "chatbot": "operational",
            "comparison": "operational",
            "education": "operational"
        },
        "version": "1.0.0"
    }
