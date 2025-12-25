"""
Subscription Service

Business logic for subscription management, entitlement checks, and usage tracking.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, extract
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from calendar import monthrange

from models import Subscription, User, ExamInstance
from models.enums import SubscriptionStatus, ExamStatus


class SubscriptionService:
    """Service for subscription and entitlement management"""

    # Define subscription plans (in production, these would be in database)
    PLANS = {
        'basic': {
            'name': 'Basic',
            'code': 'basic',
            'monthly_price': 299.00,
            'annual_price': 2999.00,
            'features': {
                'exams_per_month': 5,
                'exam_types': ['board_exam'],
                'leaderboard_access': False,
                'teacher_interaction_hours': 1,
                'direct_teacher_access': False,
                'sla_hours': 48,
                'analytics_access': 'basic',
                'report_generation': False,
                'parent_dashboard': True
            }
        },
        'premium_mcq': {
            'name': 'Premium MCQ',
            'code': 'premium_mcq',
            'monthly_price': 499.00,
            'annual_price': 4999.00,
            'features': {
                'exams_per_month': 15,
                'exam_types': ['board_exam'],  # MCQ only enforced at exam type level
                'leaderboard_access': False,
                'teacher_interaction_hours': 0,
                'direct_teacher_access': False,
                'sla_hours': 48,
                'analytics_access': 'basic',
                'report_generation': False,
                'parent_dashboard': True
            }
        },
        'premium': {
            'name': 'Premium',
            'code': 'premium',
            'monthly_price': 1999.00,
            'annual_price': None,  # Monthly only
            'features': {
                'exams_per_month': 50,
                'exam_types': ['board_exam', 'unit_wise', 'section_wise'],
                'leaderboard_access': True,
                'teacher_interaction_hours': 1,
                'direct_teacher_access': False,
                'sla_hours': 48,
                'analytics_access': 'advanced',
                'report_generation': True,
                'parent_dashboard': True
            }
        },
        'centum': {
            'name': 'Centum',
            'code': 'centum',
            'monthly_price': 2999.00,
            'annual_price': 29999.00,
            'features': {
                'exams_per_month': 50,
                'exam_types': ['board_exam', 'unit_wise', 'section_wise'],
                'leaderboard_access': True,
                'teacher_interaction_hours': 0,  # Unlimited
                'direct_teacher_access': True,
                'sla_hours': 24,
                'analytics_access': 'premium',
                'report_generation': True,
                'parent_dashboard': True
            }
        }
    }

    @staticmethod
    def get_all_plans() -> List[Dict[str, Any]]:
        """Get all available subscription plans"""
        return [
            {
                'plan_id': code,
                'plan_name': details['name'],
                'plan_code': code,
                'description': f"{details['name']} Plan",
                'monthly_price': details['monthly_price'],
                'annual_price': details.get('annual_price'),
                'currency': 'INR',
                'features': details['features'],
                'is_active': True,
                'is_popular': code == 'premium',  # Premium is popular
                'created_at': datetime.now(timezone.utc),
                'updated_at': None
            }
            for code, details in SubscriptionService.PLANS.items()
        ]

    @staticmethod
    def get_plan_by_code(plan_code: str) -> Optional[Dict[str, Any]]:
        """Get plan details by code"""
        if plan_code not in SubscriptionService.PLANS:
            return None

        details = SubscriptionService.PLANS[plan_code]
        return {
            'plan_id': plan_code,
            'plan_name': details['name'],
            'plan_code': plan_code,
            'description': f"{details['name']} Plan",
            'monthly_price': details['monthly_price'],
            'annual_price': details.get('annual_price'),
            'currency': 'INR',
            'features': details['features'],
            'is_active': True,
            'is_popular': plan_code == 'premium',
            'created_at': datetime.now(timezone.utc),
            'updated_at': None
        }

    @staticmethod
    async def create_subscription(
        session: AsyncSession,
        user_id: str,
        plan_code: str,
        billing_cycle: str,
        start_date: Optional[date] = None,
        payment_method: Optional[str] = None
    ) -> Subscription:
        """
        Create new subscription for user

        Args:
            session: Database session
            user_id: User ID
            plan_code: Plan code (basic, premium_mcq, premium, centum)
            billing_cycle: monthly or annual
            start_date: Subscription start date (defaults to today)
            payment_method: Payment method reference

        Returns:
            Created Subscription object
        """
        # Verify user exists
        user = await session.get(User, user_id)
        if not user or user.role not in ['student', 'parent']:
            raise ValueError("Invalid user or user cannot have subscription")

        # Verify plan exists
        plan = SubscriptionService.get_plan_by_code(plan_code)
        if not plan:
            raise ValueError(f"Invalid plan code: {plan_code}")

        # Validate billing cycle
        if billing_cycle == 'annual' and not plan['annual_price']:
            raise ValueError(f"Plan {plan_code} does not support annual billing")

        # Check for existing active subscription
        existing = await session.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.status == SubscriptionStatus.ACTIVE.value
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("User already has an active subscription")

        # Calculate dates
        if not start_date:
            start_date = date.today()

        if billing_cycle == 'monthly':
            # End date is last day of current month
            last_day = monthrange(start_date.year, start_date.month)[1]
            end_date = date(start_date.year, start_date.month, last_day)
        else:  # annual
            # End date is one year from start date
            end_date = date(start_date.year + 1, start_date.month, start_date.day) - timedelta(days=1)

        # Create subscription
        subscription = Subscription(
            user_id=user_id,
            plan_code=plan_code,
            billing_cycle=billing_cycle,
            start_date=start_date,
            end_date=end_date,
            status=SubscriptionStatus.ACTIVE.value,
            auto_renew=True,
            exams_used_current_month=0,
            current_month=start_date.strftime('%Y-%m')
        )

        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)

        return subscription

    @staticmethod
    async def get_user_subscription(
        session: AsyncSession,
        user_id: str
    ) -> Optional[Subscription]:
        """Get user's active subscription"""
        result = await session.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.status == SubscriptionStatus.ACTIVE.value
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def check_exam_entitlement(
        session: AsyncSession,
        user_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user can start a new exam

        Args:
            session: Database session
            user_id: User ID

        Returns:
            Tuple of (can_start, reason_if_not)
        """
        subscription = await SubscriptionService.get_user_subscription(session, user_id)

        if not subscription:
            return False, "No active subscription"

        # Check if subscription is expired
        if subscription.end_date < date.today():
            return False, "Subscription expired"

        # Get plan features
        plan = SubscriptionService.get_plan_by_code(subscription.plan_code)
        if not plan:
            return False, "Invalid subscription plan"

        features = plan['features']
        monthly_limit = features['exams_per_month']

        # Reset counter if new month
        current_month = date.today().strftime('%Y-%m')
        if subscription.current_month != current_month:
            subscription.current_month = current_month
            subscription.exams_used_current_month = 0
            await session.commit()

        # Check if limit reached
        if subscription.exams_used_current_month >= monthly_limit:
            return False, f"Monthly exam limit ({monthly_limit}) reached"

        return True, None

    @staticmethod
    async def increment_exam_usage(
        session: AsyncSession,
        user_id: str
    ) -> Subscription:
        """
        Increment exam usage counter

        Args:
            session: Database session
            user_id: User ID

        Returns:
            Updated Subscription
        """
        subscription = await SubscriptionService.get_user_subscription(session, user_id)

        if not subscription:
            raise ValueError("No active subscription")

        # Reset counter if new month
        current_month = date.today().strftime('%Y-%m')
        if subscription.current_month != current_month:
            subscription.current_month = current_month
            subscription.exams_used_current_month = 0

        subscription.exams_used_current_month += 1
        await session.commit()
        await session.refresh(subscription)

        return subscription

    @staticmethod
    async def get_subscription_usage(
        session: AsyncSession,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get current subscription usage

        Args:
            session: Database session
            user_id: User ID

        Returns:
            Dictionary with usage information
        """
        subscription = await SubscriptionService.get_user_subscription(session, user_id)

        if not subscription:
            raise ValueError("No active subscription")

        # Get plan features
        plan = SubscriptionService.get_plan_by_code(subscription.plan_code)
        features = plan['features']
        monthly_limit = features['exams_per_month']

        # Reset counter if new month
        current_month = date.today().strftime('%Y-%m')
        if subscription.current_month != current_month:
            subscription.current_month = current_month
            subscription.exams_used_current_month = 0
            await session.commit()

        exams_remaining = monthly_limit - subscription.exams_used_current_month
        usage_percentage = (subscription.exams_used_current_month / monthly_limit * 100) if monthly_limit > 0 else 0

        # Get total exams all time
        total_exams_result = await session.execute(
            select(func.count()).select_from(ExamInstance).where(
                ExamInstance.student_user_id == user_id
            )
        )
        total_exams = total_exams_result.scalar()

        # Calculate next reset date (last day of current month)
        today = date.today()
        last_day = monthrange(today.year, today.month)[1]
        next_reset = date(today.year, today.month, last_day)

        return {
            'subscription_id': str(subscription.subscription_id),
            'plan_name': plan['plan_name'],
            'current_month': subscription.current_month,
            'exams_limit': monthly_limit,
            'exams_used': subscription.exams_used_current_month,
            'exams_remaining': exams_remaining,
            'usage_percentage': round(usage_percentage, 2),
            'total_exams_all_time': total_exams,
            'avg_exams_per_month': 0,  # TODO: Calculate from history
            'is_limit_reached': exams_remaining <= 0,
            'next_reset_date': next_reset
        }

    @staticmethod
    async def check_feature_access(
        session: AsyncSession,
        user_id: str,
        feature: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user has access to a feature

        Args:
            session: Database session
            user_id: User ID
            feature: Feature name (e.g., 'leaderboard', 'reports', 'direct_teacher')

        Returns:
            Tuple of (has_access, reason_if_not)
        """
        subscription = await SubscriptionService.get_user_subscription(session, user_id)

        if not subscription:
            return False, "No active subscription"

        if subscription.end_date < date.today():
            return False, "Subscription expired"

        plan = SubscriptionService.get_plan_by_code(subscription.plan_code)
        if not plan:
            return False, "Invalid subscription plan"

        features = plan['features']

        # Map feature names to plan features
        feature_map = {
            'leaderboard': features.get('leaderboard_access', False),
            'reports': features.get('report_generation', False),
            'direct_teacher': features.get('direct_teacher_access', False),
            'advanced_analytics': features.get('analytics_access') in ['advanced', 'premium'],
            'premium_analytics': features.get('analytics_access') == 'premium'
        }

        has_access = feature_map.get(feature, False)

        if not has_access:
            return False, f"Feature '{feature}' not available in {plan['plan_name']} plan"

        return True, None

    @staticmethod
    async def get_feature_access_matrix(
        session: AsyncSession,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get user's complete feature access matrix

        Args:
            session: Database session
            user_id: User ID

        Returns:
            Dictionary with all feature access flags
        """
        subscription = await SubscriptionService.get_user_subscription(session, user_id)

        if not subscription:
            return {
                'user_id': user_id,
                'plan_name': 'None',
                'subscription_status': 'inactive',
                'can_start_exam': False,
                'exams_remaining': 0,
                'can_view_leaderboard': False,
                'can_generate_reports': False,
                'has_direct_teacher_access': False,
                'analytics_level': 'none',
                'monthly_exam_limit': 0,
                'teacher_interaction_hours': 0,
                'sla_hours': 48
            }

        plan = SubscriptionService.get_plan_by_code(subscription.plan_code)
        features = plan['features']

        # Reset counter if new month
        current_month = date.today().strftime('%Y-%m')
        if subscription.current_month != current_month:
            subscription.current_month = current_month
            subscription.exams_used_current_month = 0
            await session.commit()

        monthly_limit = features['exams_per_month']
        exams_remaining = monthly_limit - subscription.exams_used_current_month

        return {
            'user_id': user_id,
            'plan_name': plan['plan_name'],
            'subscription_status': subscription.status,
            'can_start_exam': exams_remaining > 0 and subscription.end_date >= date.today(),
            'exams_remaining': exams_remaining,
            'can_view_leaderboard': features.get('leaderboard_access', False),
            'can_generate_reports': features.get('report_generation', False),
            'has_direct_teacher_access': features.get('direct_teacher_access', False),
            'analytics_level': features.get('analytics_access', 'basic'),
            'monthly_exam_limit': monthly_limit,
            'teacher_interaction_hours': features.get('teacher_interaction_hours', 0),
            'sla_hours': features.get('sla_hours', 48)
        }

    @staticmethod
    async def cancel_subscription(
        session: AsyncSession,
        subscription_id: str,
        reason: str,
        cancel_immediately: bool = False
    ) -> Subscription:
        """
        Cancel subscription

        Args:
            session: Database session
            subscription_id: Subscription ID
            reason: Cancellation reason
            cancel_immediately: Cancel now vs end of billing period

        Returns:
            Updated Subscription
        """
        subscription = await session.get(Subscription, subscription_id)

        if not subscription:
            raise ValueError("Subscription not found")

        if subscription.status == SubscriptionStatus.CANCELLED.value:
            raise ValueError("Subscription already cancelled")

        if cancel_immediately:
            subscription.status = SubscriptionStatus.CANCELLED.value
            subscription.end_date = date.today()
        else:
            # Cancel at end of billing period
            subscription.auto_renew = False
            # Status will change to cancelled after end_date

        await session.commit()
        await session.refresh(subscription)

        return subscription

    @staticmethod
    async def update_subscription(
        session: AsyncSession,
        subscription_id: str,
        plan_code: Optional[str] = None,
        billing_cycle: Optional[str] = None,
        auto_renew: Optional[bool] = None
    ) -> Subscription:
        """
        Update subscription (upgrade/downgrade)

        Args:
            session: Database session
            subscription_id: Subscription ID
            plan_code: New plan code (for upgrade/downgrade)
            billing_cycle: New billing cycle
            auto_renew: Enable/disable auto-renewal

        Returns:
            Updated Subscription
        """
        subscription = await session.get(Subscription, subscription_id)

        if not subscription:
            raise ValueError("Subscription not found")

        if subscription.status != SubscriptionStatus.ACTIVE.value:
            raise ValueError("Can only update active subscriptions")

        # Update plan (upgrade/downgrade)
        if plan_code and plan_code != subscription.plan_code:
            plan = SubscriptionService.get_plan_by_code(plan_code)
            if not plan:
                raise ValueError(f"Invalid plan code: {plan_code}")

            subscription.plan_code = plan_code
            # Reset usage for new plan
            subscription.exams_used_current_month = 0

        # Update billing cycle
        if billing_cycle and billing_cycle != subscription.billing_cycle:
            subscription.billing_cycle = billing_cycle

        # Update auto-renew
        if auto_renew is not None:
            subscription.auto_renew = auto_renew

        await session.commit()
        await session.refresh(subscription)

        return subscription

    @staticmethod
    async def get_subscription_stats(
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get system-wide subscription statistics

        Args:
            session: Database session

        Returns:
            Dictionary with subscription stats
        """
        # Total subscriptions
        total_result = await session.execute(
            select(func.count()).select_from(Subscription)
        )
        total = total_result.scalar()

        # By status
        active_result = await session.execute(
            select(func.count()).select_from(Subscription).where(
                Subscription.status == SubscriptionStatus.ACTIVE.value
            )
        )
        active = active_result.scalar()

        expired_result = await session.execute(
            select(func.count()).select_from(Subscription).where(
                Subscription.status == SubscriptionStatus.EXPIRED.value
            )
        )
        expired = expired_result.scalar()

        cancelled_result = await session.execute(
            select(func.count()).select_from(Subscription).where(
                Subscription.status == SubscriptionStatus.CANCELLED.value
            )
        )
        cancelled = cancelled_result.scalar()

        # By plan
        all_subs_result = await session.execute(select(Subscription))
        all_subs = all_subs_result.scalars().all()

        by_plan = {}
        for sub in all_subs:
            plan_code = sub.plan_code
            by_plan[plan_code] = by_plan.get(plan_code, 0) + 1

        # New this month
        today = date.today()
        first_of_month = date(today.year, today.month, 1)

        new_this_month_result = await session.execute(
            select(func.count()).select_from(Subscription).where(
                Subscription.created_at >= first_of_month
            )
        )
        new_this_month = new_this_month_result.scalar()

        return {
            'total_subscriptions': total,
            'active_subscriptions': active,
            'expired_subscriptions': expired,
            'cancelled_subscriptions': cancelled,
            'subscriptions_by_plan': by_plan,
            'total_revenue_this_month': 0,  # TODO: Calculate from payments
            'total_revenue_all_time': 0,  # TODO: Calculate from payments
            'new_subscriptions_this_month': new_this_month,
            'cancellations_this_month': 0,  # TODO: Track cancellation dates
            'renewal_rate': 0  # TODO: Calculate renewal rate
        }


# Global subscription service instance
subscription_service = SubscriptionService()
