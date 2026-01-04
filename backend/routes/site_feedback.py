"""
Site Feedback Routes

Endpoints for general website feedback submission and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid
from slowapi import Limiter
from slowapi.util import get_remote_address

from database import get_session
from models.site_feedback import SiteFeedback, FeedbackCategory, FeedbackStatus
from models.user import User
from dependencies import get_current_user_optional, get_current_admin

router = APIRouter(prefix="/feedback", tags=["Site Feedback"])

# Rate limiter for feedback endpoints
feedback_limiter = Limiter(key_func=get_remote_address)


# ============================================
# Pydantic Schemas
# ============================================

class FeedbackSubmitRequest(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    type: str = FeedbackCategory.OTHER.value
    message: str = Field(..., min_length=10, max_length=2000)
    email: Optional[EmailStr] = None
    page: Optional[str] = None


class FeedbackSubmitResponse(BaseModel):
    success: bool
    message: str
    feedback_id: str


class FeedbackResponse(BaseModel):
    id: str
    user_id: Optional[str]
    email: Optional[str]
    rating: Optional[int]
    category: str
    message: str
    page_url: Optional[str]
    status: str
    admin_notes: Optional[str]
    created_at: datetime


class FeedbackUpdateRequest(BaseModel):
    status: Optional[str] = None
    admin_notes: Optional[str] = None


# ============================================
# Public Endpoint
# ============================================

@router.post("/", response_model=FeedbackSubmitResponse, status_code=status.HTTP_201_CREATED)
@feedback_limiter.limit("5/minute")  # Prevent feedback spam
async def submit_feedback(
    request: FeedbackSubmitRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Submit site feedback.
    Can be called by authenticated or unauthenticated users.
    """
    # Validate category
    valid_categories = [c.value for c in FeedbackCategory]
    category = request.type if request.type in valid_categories else FeedbackCategory.OTHER.value

    # Get IP and user agent
    client_ip = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent", "")[:500]

    feedback = SiteFeedback(
        user_id=current_user.user_id if current_user else None,
        email=request.email or (current_user.email if current_user else None),
        rating=request.rating,
        category=category,
        message=request.message,
        page_url=request.page,
        user_agent=user_agent,
        ip_address=client_ip,
        status=FeedbackStatus.NEW.value
    )

    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    return FeedbackSubmitResponse(
        success=True,
        message="Thank you for your feedback!",
        feedback_id=str(feedback.id)
    )


# ============================================
# Admin Endpoints
# ============================================

@router.get("/", response_model=List[FeedbackResponse])
async def list_feedback(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin)
):
    """List all feedback (admin only)"""
    query = select(SiteFeedback).order_by(SiteFeedback.created_at.desc())

    if status_filter:
        query = query.where(SiteFeedback.status == status_filter)

    if category_filter:
        query = query.where(SiteFeedback.category == category_filter)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    feedbacks = result.scalars().all()

    return [
        FeedbackResponse(
            id=str(f.id),
            user_id=str(f.user_id) if f.user_id else None,
            email=f.email,
            rating=f.rating,
            category=f.category,
            message=f.message,
            page_url=f.page_url,
            status=f.status,
            admin_notes=f.admin_notes,
            created_at=f.created_at
        )
        for f in feedbacks
    ]


@router.get("/stats")
async def get_feedback_stats(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin)
):
    """Get feedback statistics (admin only)"""
    from sqlalchemy import func

    # Total count
    result = await db.execute(select(func.count(SiteFeedback.id)))
    total = result.scalar()

    # Count by status
    status_counts = {}
    for status in FeedbackStatus:
        result = await db.execute(
            select(func.count(SiteFeedback.id)).where(SiteFeedback.status == status.value)
        )
        status_counts[status.value] = result.scalar()

    # Count by category
    category_counts = {}
    for category in FeedbackCategory:
        result = await db.execute(
            select(func.count(SiteFeedback.id)).where(SiteFeedback.category == category.value)
        )
        category_counts[category.value] = result.scalar()

    # Average rating
    result = await db.execute(
        select(func.avg(SiteFeedback.rating)).where(SiteFeedback.rating.isnot(None))
    )
    avg_rating = result.scalar()

    return {
        "total": total,
        "by_status": status_counts,
        "by_category": category_counts,
        "average_rating": round(avg_rating, 2) if avg_rating else None
    }


@router.patch("/{feedback_id}")
async def update_feedback(
    feedback_id: str,
    request: FeedbackUpdateRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin)
):
    """Update feedback status/notes (admin only)"""
    result = await db.execute(
        select(SiteFeedback).where(SiteFeedback.id == uuid.UUID(feedback_id))
    )
    feedback = result.scalar_one_or_none()

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )

    if request.status:
        valid_statuses = [s.value for s in FeedbackStatus]
        if request.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {valid_statuses}"
            )
        feedback.status = request.status

        # Set reviewed info if moving from NEW
        if feedback.reviewed_by is None:
            feedback.reviewed_by = current_user.user_id
            feedback.reviewed_at = datetime.now()

    if request.admin_notes is not None:
        feedback.admin_notes = request.admin_notes

    await db.commit()

    return {
        "success": True,
        "feedback_id": str(feedback.id),
        "status": feedback.status
    }


@router.delete("/{feedback_id}")
async def delete_feedback(
    feedback_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin)
):
    """Delete feedback (admin only)"""
    result = await db.execute(
        select(SiteFeedback).where(SiteFeedback.id == uuid.UUID(feedback_id))
    )
    feedback = result.scalar_one_or_none()

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )

    await db.delete(feedback)
    await db.commit()

    return {
        "success": True,
        "message": "Feedback deleted"
    }
