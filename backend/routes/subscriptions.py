"""
Subscription Routes

API endpoints for subscription management and entitlement enforcement.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from database import get_session
from models import User, Subscription
from dependencies.auth import (
    require_student, require_admin,
    require_student_or_parent, get_current_active_user
)
from schemas.subscription import (
    SubscriptionPlanListResponse,
    SubscriptionPlanResponse,
    SubscriptionPlanFeatures,
    CreateSubscriptionRequest,
    UpdateSubscriptionRequest,
    SubscriptionResponse,
    SubscriptionUsageResponse,
    SubscriptionHistoryResponse,
    EntitlementCheckRequest,
    EntitlementCheckResponse,
    FeatureAccessResponse,
    CancelSubscriptionRequest,
    CancelSubscriptionResponse,
    SubscriptionStatsResponse,
    GrantTrialRequest,
    GrantTrialResponse
)
from services import subscription_service


router = APIRouter()


# ==================== Subscription Plans ====================

@router.get("/subscription-plans", response_model=SubscriptionPlanListResponse)
async def get_subscription_plans():
    """
    Get all available subscription plans

    - Shows all plan tiers with features
    - Public endpoint (no auth required)
    - Used for plan selection during registration

    **Permissions**: Public
    """
    plans = subscription_service.get_all_plans()

    plan_responses = []
    for plan in plans:
        plan_responses.append(SubscriptionPlanResponse(
            plan_id=plan['plan_id'],
            plan_name=plan['plan_name'],
            plan_code=plan['plan_code'],
            description=plan['description'],
            monthly_price=plan['monthly_price'],
            annual_price=plan['annual_price'],
            currency=plan['currency'],
            features=SubscriptionPlanFeatures(**plan['features']),
            is_active=plan['is_active'],
            is_popular=plan['is_popular'],
            created_at=plan['created_at'],
            updated_at=plan['updated_at']
        ))

    return SubscriptionPlanListResponse(plans=plan_responses)


@router.get("/subscription-plans/{plan_code}", response_model=SubscriptionPlanResponse)
async def get_subscription_plan(plan_code: str):
    """
    Get specific subscription plan details

    **Permissions**: Public
    """
    plan = subscription_service.get_plan_by_code(plan_code)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_code}"
        )

    return SubscriptionPlanResponse(
        plan_id=plan['plan_id'],
        plan_name=plan['plan_name'],
        plan_code=plan['plan_code'],
        description=plan['description'],
        monthly_price=plan['monthly_price'],
        annual_price=plan['annual_price'],
        currency=plan['currency'],
        features=SubscriptionPlanFeatures(**plan['features']),
        is_active=plan['is_active'],
        is_popular=plan['is_popular'],
        created_at=plan['created_at'],
        updated_at=plan['updated_at']
    )


# ==================== User Subscriptions ====================

@router.post("/subscriptions", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Create new subscription for user (Admin only)

    - Assigns subscription plan to user
    - Validates plan and billing cycle
    - Checks for existing active subscriptions
    - Sets up usage tracking

    **Permissions**: Admins only
    """
    try:
        subscription = await subscription_service.create_subscription(
            session,
            request.user_id,
            request.plan_id,
            request.billing_cycle,
            request.start_date,
            request.payment_method
        )

        plan = subscription_service.get_plan_by_code(subscription.plan_code)

        # Get usage info
        usage = await subscription_service.get_subscription_usage(session, request.user_id)

        return SubscriptionResponse(
            subscription_id=str(subscription.subscription_id),
            user_id=str(subscription.user_id),
            plan_id=subscription.plan_code,
            plan_name=plan['plan_name'],
            billing_cycle=subscription.billing_cycle,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            renewal_date=None,  # TODO: Calculate
            status=subscription.status,
            auto_renew=subscription.auto_renew,
            exams_used_this_month=subscription.exams_used_current_month,
            exams_remaining_this_month=usage['exams_remaining'],
            current_month=subscription.current_month,
            last_payment_date=None,
            last_payment_amount=None,
            next_payment_date=None,
            next_payment_amount=None,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/subscriptions/my", response_model=SubscriptionResponse)
async def get_my_subscription(
    current_user: User = Depends(require_student_or_parent),
    session: AsyncSession = Depends(get_session)
):
    """
    Get my current subscription

    - Shows active subscription details
    - Includes usage information
    - Available to students and parents

    **Permissions**: Students and Parents
    """
    subscription = await subscription_service.get_user_subscription(
        session,
        str(current_user.user_id)
    )

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )

    plan = subscription_service.get_plan_by_code(subscription.plan_code)
    usage = await subscription_service.get_subscription_usage(session, str(current_user.user_id))

    return SubscriptionResponse(
        subscription_id=str(subscription.subscription_id),
        user_id=str(subscription.user_id),
        plan_id=subscription.plan_code,
        plan_name=plan['plan_name'],
        billing_cycle=subscription.billing_cycle,
        start_date=subscription.start_date,
        end_date=subscription.end_date,
        renewal_date=None,
        status=subscription.status,
        auto_renew=subscription.auto_renew,
        exams_used_this_month=subscription.exams_used_current_month,
        exams_remaining_this_month=usage['exams_remaining'],
        current_month=subscription.current_month,
        last_payment_date=None,
        last_payment_amount=None,
        next_payment_date=None,
        next_payment_amount=None,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at
    )


@router.get("/subscriptions/my/usage", response_model=SubscriptionUsageResponse)
async def get_my_subscription_usage(
    current_user: User = Depends(require_student),
    session: AsyncSession = Depends(get_session)
):
    """
    Get my subscription usage

    - Current month usage
    - Exams remaining
    - Historical usage

    **Permissions**: Students only
    """
    try:
        usage = await subscription_service.get_subscription_usage(
            session,
            str(current_user.user_id)
        )

        return SubscriptionUsageResponse(**usage)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: str,
    request: UpdateSubscriptionRequest,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Update subscription (Admin only)

    - Upgrade/downgrade plan
    - Change billing cycle
    - Enable/disable auto-renewal

    **Permissions**: Admins only
    """
    try:
        subscription = await subscription_service.update_subscription(
            session,
            subscription_id,
            request.plan_id,
            request.billing_cycle,
            request.auto_renew
        )

        plan = subscription_service.get_plan_by_code(subscription.plan_code)
        usage = await subscription_service.get_subscription_usage(session, str(subscription.user_id))

        return SubscriptionResponse(
            subscription_id=str(subscription.subscription_id),
            user_id=str(subscription.user_id),
            plan_id=subscription.plan_code,
            plan_name=plan['plan_name'],
            billing_cycle=subscription.billing_cycle,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            renewal_date=None,
            status=subscription.status,
            auto_renew=subscription.auto_renew,
            exams_used_this_month=subscription.exams_used_current_month,
            exams_remaining_this_month=usage['exams_remaining'],
            current_month=subscription.current_month,
            last_payment_date=None,
            last_payment_amount=None,
            next_payment_date=None,
            next_payment_amount=None,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/subscriptions/{subscription_id}/cancel", response_model=CancelSubscriptionResponse)
async def cancel_subscription(
    subscription_id: str,
    request: CancelSubscriptionRequest,
    current_user: User = Depends(require_student_or_parent),
    session: AsyncSession = Depends(get_session)
):
    """
    Cancel subscription

    - Cancel immediately or at end of billing period
    - Requires cancellation reason
    - User can cancel own subscription

    **Permissions**: Students and Parents (own subscription)
    """
    try:
        # Verify ownership
        subscription = await session.get(Subscription, subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        if str(subscription.user_id) != str(current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only cancel own subscription"
            )

        cancelled_sub = await subscription_service.cancel_subscription(
            session,
            subscription_id,
            request.reason,
            request.cancel_immediately
        )

        return CancelSubscriptionResponse(
            subscription_id=str(cancelled_sub.subscription_id),
            status=cancelled_sub.status,
            cancelled_at=cancelled_sub.updated_at,
            access_until=cancelled_sub.end_date,
            refund_amount=None,  # TODO: Calculate refund
            refund_status=None
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== Entitlements ====================

@router.get("/entitlements/check-exam")
async def check_exam_entitlement(
    current_user: User = Depends(require_student),
    session: AsyncSession = Depends(get_session)
):
    """
    Check if user can start a new exam

    - Checks subscription status
    - Checks monthly exam limit
    - Returns detailed reason if not entitled

    **Permissions**: Students only
    """
    can_start, reason = await subscription_service.check_exam_entitlement(
        session,
        str(current_user.user_id)
    )

    subscription = await subscription_service.get_user_subscription(session, str(current_user.user_id))

    plan_name = "None"
    if subscription:
        plan = subscription_service.get_plan_by_code(subscription.plan_code)
        plan_name = plan['plan_name'] if plan else "Unknown"

    return EntitlementCheckResponse(
        user_id=str(current_user.user_id),
        feature="start_exam",
        is_entitled=can_start,
        reason=reason,
        subscription_status=subscription.status if subscription else "inactive",
        plan_name=plan_name,
        usage_info=None
    )


@router.get("/entitlements/feature-access", response_model=FeatureAccessResponse)
async def get_feature_access(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get complete feature access matrix

    - Shows all features user has access to
    - Includes usage limits
    - Available to all users

    **Permissions**: All authenticated users
    """
    access = await subscription_service.get_feature_access_matrix(
        session,
        str(current_user.user_id)
    )

    return FeatureAccessResponse(**access)


# ==================== Admin ====================

@router.get("/subscriptions/stats", response_model=SubscriptionStatsResponse)
async def get_subscription_stats(
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Get subscription statistics (Admin only)

    - Total subscriptions by status
    - Subscriptions by plan
    - Revenue metrics
    - Renewal rates

    **Permissions**: Admins only
    """
    stats = await subscription_service.get_subscription_stats(session)

    return SubscriptionStatsResponse(
        total_subscriptions=stats['total_subscriptions'],
        active_subscriptions=stats['active_subscriptions'],
        expired_subscriptions=stats['expired_subscriptions'],
        cancelled_subscriptions=stats['cancelled_subscriptions'],
        subscriptions_by_plan=stats['subscriptions_by_plan'],
        total_revenue_this_month=stats['total_revenue_this_month'],
        total_revenue_all_time=stats['total_revenue_all_time'],
        new_subscriptions_this_month=stats['new_subscriptions_this_month'],
        cancellations_this_month=stats['cancellations_this_month'],
        renewal_rate=stats['renewal_rate']
    )


@router.post("/subscriptions/grant-trial", response_model=GrantTrialResponse)
async def grant_trial(
    request: GrantTrialRequest,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Grant trial subscription to user (Admin only)

    - Creates time-limited trial subscription
    - Default 7 days, max 30 days
    - Useful for user acquisition

    **Permissions**: Admins only
    """
    try:
        from datetime import timedelta

        # Create subscription with trial end date
        trial_end = date.today() + timedelta(days=request.trial_days)

        subscription = await subscription_service.create_subscription(
            session,
            request.user_id,
            request.plan_id,
            'monthly',
            start_date=date.today()
        )

        # Update end date for trial
        subscription.end_date = trial_end
        await session.commit()

        plan = subscription_service.get_plan_by_code(subscription.plan_code)

        return GrantTrialResponse(
            subscription_id=str(subscription.subscription_id),
            user_id=str(subscription.user_id),
            plan_name=plan['plan_name'],
            trial_end_date=trial_end,
            status=subscription.status
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
