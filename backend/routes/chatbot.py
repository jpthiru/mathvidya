"""
Chatbot Routes

Endpoints for the Mathvidya chatbot with RAG (Retrieval-Augmented Generation).
Supports two modes:
1. RAG mode: Uses vector embeddings + LLM for intelligent responses
2. Simple mode: Rule-based FAQ matching (fallback if RAG models unavailable)
"""

import logging
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, List
from slowapi import Limiter
from slowapi.util import get_remote_address

from config.settings import settings

logger = logging.getLogger(__name__)

# Try to use RAG service, fall back to simple FAQ service
try:
    from services.rag_chatbot_service import generate_response, get_suggested_questions
    RAG_ENABLED = True
    logger.info("RAG chatbot service loaded")
except ImportError as e:
    from services.chatbot_service import generate_response, get_suggested_questions
    RAG_ENABLED = False
    logger.warning(f"RAG service unavailable, using simple FAQ: {e}")

router = APIRouter(prefix="/chat", tags=["Chatbot"])

# Rate limiter for chat endpoints
chat_limiter = Limiter(key_func=get_remote_address)


# ============================================
# Pydantic Schemas
# ============================================

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


class ChatResponse(BaseModel):
    response: str
    confidence: float
    matched_question: Optional[str] = None
    source: str  # "faq", "greeting", "fallback", "validation"


class SuggestedQuestionsResponse(BaseModel):
    questions: List[str]


class ChatStatusResponse(BaseModel):
    status: str
    mode: str  # "rag" or "simple"
    rag_enabled: bool
    embedding_model: Optional[str] = None
    llm_model: Optional[str] = None


# ============================================
# Endpoints
# ============================================

@router.post("/", response_model=ChatResponse)
@chat_limiter.limit("30/minute")  # Reasonable rate limit for chat
async def chat(
    chat_request: ChatRequest,
    request: Request  # Must be named 'request' for slowapi rate limiter
):
    """
    Send a message to the chatbot and get a response.

    This is a public endpoint - no authentication required.

    Uses RAG (Retrieval-Augmented Generation) when available:
    - Sentence transformers for semantic search
    - FAISS for vector similarity
    - Optional LLM for natural responses

    Falls back to rule-based FAQ matching if RAG models aren't available.
    """
    try:
        result = generate_response(chat_request.message)

        return ChatResponse(
            response=result["response"],
            confidence=result["confidence"],
            matched_question=result["matched_question"],
            source=result["source"]
        )
    except Exception as e:
        logger.error(f"Chatbot error: {e}")
        # Return a friendly error response instead of crashing
        return ChatResponse(
            response="I'm having trouble processing your request right now. Please try again or contact support@mathvidya.com for assistance.",
            confidence=0.0,
            matched_question=None,
            source="error"
        )


@router.get("/suggestions", response_model=SuggestedQuestionsResponse)
async def get_suggestions():
    """
    Get a list of suggested questions for the chat interface.

    This is a public endpoint - no authentication required.
    """
    questions = get_suggested_questions()

    return SuggestedQuestionsResponse(questions=questions)


@router.get("/status", response_model=ChatStatusResponse)
async def get_chat_status():
    """
    Get the current status of the chatbot service.

    Returns information about whether RAG is enabled and which models are loaded.
    """
    if RAG_ENABLED:
        from services.rag_chatbot_service import EMBEDDING_MODEL, LLM_MODEL
        return ChatStatusResponse(
            status="online",
            mode="rag",
            rag_enabled=True,
            embedding_model=EMBEDDING_MODEL,
            llm_model=LLM_MODEL
        )
    else:
        return ChatStatusResponse(
            status="online",
            mode="simple",
            rag_enabled=False,
            embedding_model=None,
            llm_model=None
        )
