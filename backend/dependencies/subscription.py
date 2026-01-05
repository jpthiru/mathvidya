"""
Subscription Dependencies

FastAPI dependencies for enforcing subscription limits.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from models import User
from dependencies.auth import get_current_active_user
from services.subscription_enforcement import SubscriptionEnforcement


async def check_exam_creation_allowed(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> dict:
    """
    Dependency to check if user can create a new exam.

    Raises HTTPException if limit reached.

    Returns:
        Usage summary dict if allowed
    """
    enforcer = SubscriptionEnforcement(db)
    limit_check = await enforcer.check_exam_limit(current_user.user_id)

    if not limit_check["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "exam_limit_reached",
                "message": limit_check["reason"],
                "exams_used": limit_check["exams_used"],
                "exams_limit": limit_check["exams_limit"],
                "period_end": limit_check.get("period_end"),
                "subscription_plan": limit_check.get("subscription_plan")
            }
        )

    return limit_check


async def get_subscription_usage(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> dict:
    """
    Dependency to get subscription usage summary.

    Does not enforce limits, just returns info.

    Returns:
        Usage summary dict
    """
    enforcer = SubscriptionEnforcement(db)
    return await enforcer.get_usage_summary(current_user.user_id)
