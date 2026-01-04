"""
Chatbot Routes

Endpoints for the Mathvidya FAQ chatbot.
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, List
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.chatbot_service import generate_response, get_suggested_questions

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


# ============================================
# Endpoints
# ============================================

@router.post("/", response_model=ChatResponse)
@chat_limiter.limit("30/minute")  # Reasonable rate limit for chat
async def chat(
    request: ChatRequest,
    http_request: Request
):
    """
    Send a message to the chatbot and get a response.

    This is a public endpoint - no authentication required.
    Uses rule-based FAQ matching for instant, cost-free responses.
    """
    result = generate_response(request.message)

    return ChatResponse(
        response=result["response"],
        confidence=result["confidence"],
        matched_question=result["matched_question"],
        source=result["source"]
    )


@router.get("/suggestions", response_model=SuggestedQuestionsResponse)
async def get_suggestions():
    """
    Get a list of suggested questions for the chat interface.

    This is a public endpoint - no authentication required.
    """
    questions = get_suggested_questions()

    return SuggestedQuestionsResponse(questions=questions)
