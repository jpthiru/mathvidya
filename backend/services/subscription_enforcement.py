"""
Subscription Enforcement Service

Enforces subscription limits and entitlements for exam creation.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from models import Subscription, ExamInstance, SubscriptionPlan, User
from datetime import datetime, timedelta
from typing import Optional
import uuid


class SubscriptionEnforcement:
    """
    Service for enforcing subscription limits.

    Tracks exam usage against monthly limits.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_subscription(self, user_id: uuid.UUID) -> Optional[Subscription]:
        """
        Get user's active subscription.

        Args:
            user_id: User UUID

        Returns:
            Active Subscription or None
        """
        result = await self.db.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.subscription_status == "active"
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_current_billing_period_dates(
        self,
        subscription: Subscription
    ) -> tuple[datetime, datetime]:
        """
        Get start and end dates of current billing period.

        Args:
            subscription: Subscription object

        Returns:
            (period_start, period_end) as datetime objects
        """
        # Parse subscription start date
        start_date = datetime.fromisoformat(subscription.start_date.replace('Z', '+00:00'))

        # Calculate current period based on 30-day cycles
        now = datetime.utcnow()
        days_since_start = (now - start_date).days
        period_number = days_since_start // 30

        period_start = start_date + timedelta(days=period_number * 30)
        period_end = period_start + timedelta(days=30)

        return period_start, period_end

    async def get_exams_used_this_period(
        self,
        user_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime
    ) -> int:
        """
        Count exams created in current billing period.

        Args:
            user_id: User UUID
            period_start: Period start date
            period_end: Period end date

        Returns:
            Number of exams created
        """
        period_start_iso = period_start.isoformat()
        period_end_iso = period_end.isoformat()

        result = await self.db.execute(
            select(func.count(ExamInstance.exam_instance_id)).where(
                and_(
                    ExamInstance.student_id == user_id,
                    ExamInstance.started_at >= period_start_iso,
                    ExamInstance.started_at < period_end_iso
                )
            )
        )
        return result.scalar() or 0

    async def check_exam_limit(
        self,
        user_id: uuid.UUID
    ) -> dict:
        """
        Check if user can create a new exam.

        Args:
            user_id: User UUID

        Returns:
            dict with:
                - allowed: bool
                - reason: str (if not allowed)
                - exams_used: int
                - exams_limit: int
                - exams_remaining: int
                - period_start: str
                - period_end: str
                - subscription_plan: str
        """
        # Get active subscription
        subscription = await self.get_active_subscription(user_id)

        if not subscription:
            return {
                "allowed": False,
                "reason": "No active subscription found. Please subscribe to a plan.",
                "exams_used": 0,
                "exams_limit": 0,
                "exams_remaining": 0,
                "subscription_plan": None
            }

        # Get plan details
        result = await self.db.execute(
            select(SubscriptionPlan).where(
                SubscriptionPlan.plan_type == subscription.plan_type
            )
        )
        plan = result.scalar_one_or_none()

        if not plan:
            return {
                "allowed": False,
                "reason": "Subscription plan not found. Please contact support.",
                "exams_used": 0,
                "exams_limit": 0,
                "exams_remaining": 0,
                "subscription_plan": subscription.plan_type
            }

        # Get current billing period
        period_start, period_end = await self.get_current_billing_period_dates(subscription)

        # Count exams used this period
        exams_used = await self.get_exams_used_this_period(user_id, period_start, period_end)

        # Check limit
        exams_limit = plan.exams_per_month
        exams_remaining = max(0, exams_limit - exams_used)

        allowed = exams_used < exams_limit

        return {
            "allowed": allowed,
            "reason": f"Monthly exam limit reached ({exams_used}/{exams_limit}). Your limit will reset on {period_end.strftime('%Y-%m-%d')}." if not allowed else None,
            "exams_used": exams_used,
            "exams_limit": exams_limit,
            "exams_remaining": exams_remaining,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "subscription_plan": plan.plan_name,
            "plan_type": subscription.plan_type
        }

    async def get_usage_summary(
        self,
        user_id: uuid.UUID
    ) -> dict:
        """
        Get complete usage summary for user.

        Useful for displaying on dashboard.

        Returns:
            dict with usage statistics
        """
        limit_check = await self.check_exam_limit(user_id)

        return {
            "subscription_plan": limit_check.get("subscription_plan"),
            "plan_type": limit_check.get("plan_type"),
            "exams_used": limit_check["exams_used"],
            "exams_limit": limit_check["exams_limit"],
            "exams_remaining": limit_check["exams_remaining"],
            "current_period_start": limit_check.get("period_start"),
            "current_period_end": limit_check.get("period_end"),
            "can_create_exam": limit_check["allowed"]
        }
