"""
Subscription Usage Routes

API endpoints for checking subscription usage and limits.
"""

from fastapi import APIRouter, Depends
from dependencies.subscription import get_subscription_usage
from pydantic import BaseModel


router = APIRouter(prefix="/api/v1/subscription", tags=["Subscription Usage"])


class SubscriptionUsageResponse(BaseModel):
    """Subscription usage summary"""
    subscription_plan: str
    plan_type: str
    exams_used: int
    exams_limit: int
    exams_remaining: int
    current_period_start: str
    current_period_end: str
    can_create_exam: bool


@router.get("/usage", response_model=SubscriptionUsageResponse)
async def get_my_subscription_usage(
    usage: dict = Depends(get_subscription_usage)
):
    """
    Get current user's subscription usage summary.

    Returns:
        - Plan details
        - Exams used this billing period
        - Exams remaining
        - Period dates
        - Whether user can create new exams
    """
    return SubscriptionUsageResponse(**usage)
