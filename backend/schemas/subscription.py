"""
Subscription Schemas

Pydantic models for subscription management and entitlement enforcement.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# ==================== Subscription Plans ====================

class SubscriptionPlanFeatures(BaseModel):
    """Features included in a subscription plan"""
    exams_per_month: int = Field(..., ge=0, description="Monthly exam limit")
    exam_types: List[str] = Field(
        default_factory=list,
        description="Allowed exam types: board_exam, unit_wise, section_wise"
    )
    leaderboard_access: bool = Field(default=False, description="Can view leaderboard")
    teacher_interaction_hours: int = Field(default=0, ge=0, description="Monthly teacher interaction hours")
    direct_teacher_access: bool = Field(default=False, description="Direct teacher messaging")
    sla_hours: int = Field(default=48, description="Evaluation SLA (24 or 48 hours)")
    analytics_access: str = Field(
        default="basic",
        description="Analytics level: basic, advanced, premium"
    )
    report_generation: bool = Field(default=False, description="Can generate detailed reports")
    parent_dashboard: bool = Field(default=True, description="Parent has dashboard access")

    @validator('sla_hours')
    def validate_sla(cls, v):
        """Ensure SLA is 24 or 48 hours"""
        if v not in [24, 48]:
            raise ValueError("SLA must be 24 or 48 hours")
        return v


class SubscriptionPlanResponse(BaseModel):
    """Subscription plan details"""
    plan_id: str
    plan_name: str
    plan_code: str  # basic, premium_mcq, premium, centum
    description: str

    # Pricing
    monthly_price: float
    annual_price: Optional[float]
    currency: str = "INR"

    # Features
    features: SubscriptionPlanFeatures

    # Status
    is_active: bool
    is_popular: bool = False

    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class SubscriptionPlanListResponse(BaseModel):
    """List of available subscription plans"""
    plans: List[SubscriptionPlanResponse]


# ==================== User Subscriptions ====================

class CreateSubscriptionRequest(BaseModel):
    """Create new subscription for user"""
    user_id: str
    plan_id: str
    billing_cycle: str = Field(..., pattern="^(monthly|annual)$", description="Billing cycle")
    start_date: Optional[date] = Field(None, description="Start date (defaults to today)")
    payment_method: Optional[str] = Field(None, description="Payment method reference")
    coupon_code: Optional[str] = Field(None, description="Discount coupon")


class UpdateSubscriptionRequest(BaseModel):
    """Update existing subscription"""
    plan_id: Optional[str] = Field(None, description="Upgrade/downgrade to different plan")
    billing_cycle: Optional[str] = Field(None, pattern="^(monthly|annual)$")
    auto_renew: Optional[bool] = Field(None, description="Enable/disable auto-renewal")


class SubscriptionResponse(BaseModel):
    """User subscription details"""
    subscription_id: str
    user_id: str
    plan_id: str
    plan_name: str

    # Billing
    billing_cycle: str  # monthly, annual
    start_date: date
    end_date: date
    renewal_date: Optional[date]

    # Status
    status: str  # active, expired, cancelled, suspended
    auto_renew: bool

    # Usage
    exams_used_this_month: int
    exams_remaining_this_month: int
    current_month: str  # YYYY-MM

    # Payment
    last_payment_date: Optional[date]
    last_payment_amount: Optional[float]
    next_payment_date: Optional[date]
    next_payment_amount: Optional[float]

    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class SubscriptionUsageResponse(BaseModel):
    """Current subscription usage"""
    subscription_id: str
    plan_name: str

    # Current month
    current_month: str
    exams_limit: int
    exams_used: int
    exams_remaining: int
    usage_percentage: float

    # Historical
    total_exams_all_time: int
    avg_exams_per_month: float

    # Status
    is_limit_reached: bool
    next_reset_date: date


class SubscriptionHistoryEntry(BaseModel):
    """Single subscription history entry"""
    subscription_id: str
    plan_name: str
    start_date: date
    end_date: date
    status: str
    total_exams: int


class SubscriptionHistoryResponse(BaseModel):
    """User's subscription history"""
    user_id: str
    current_subscription: Optional[SubscriptionResponse]
    history: List[SubscriptionHistoryEntry] = Field(default_factory=list)


# ==================== Entitlements ====================

class EntitlementCheckRequest(BaseModel):
    """Request to check user entitlement"""
    user_id: str
    feature: str = Field(
        ...,
        description="Feature to check: start_exam, view_leaderboard, generate_report, etc."
    )
    metadata: Optional[dict] = Field(None, description="Additional context for check")


class EntitlementCheckResponse(BaseModel):
    """Result of entitlement check"""
    user_id: str
    feature: str
    is_entitled: bool
    reason: Optional[str] = Field(None, description="Reason if not entitled")

    # Additional info
    subscription_status: str
    plan_name: str
    usage_info: Optional[dict] = None


class FeatureAccessResponse(BaseModel):
    """User's feature access matrix"""
    user_id: str
    plan_name: str
    subscription_status: str

    # Features
    can_start_exam: bool
    exams_remaining: int
    can_view_leaderboard: bool
    can_generate_reports: bool
    has_direct_teacher_access: bool
    analytics_level: str

    # Limits
    monthly_exam_limit: int
    teacher_interaction_hours: int
    sla_hours: int


# ==================== Payments ====================

class CreatePaymentRequest(BaseModel):
    """Record a payment"""
    subscription_id: str
    amount: Decimal = Field(..., ge=0, description="Payment amount")
    payment_method: str = Field(..., description="Payment method: card, upi, netbanking")
    transaction_id: str = Field(..., description="External payment transaction ID")
    payment_gateway: str = Field(..., description="Payment gateway: razorpay, stripe, etc.")
    currency: str = Field(default="INR")


class PaymentResponse(BaseModel):
    """Payment record"""
    payment_id: str
    subscription_id: str
    user_id: str

    amount: float
    currency: str
    payment_method: str
    payment_gateway: str
    transaction_id: str

    status: str  # pending, completed, failed, refunded
    paid_at: Optional[datetime]

    created_at: datetime

    class Config:
        from_attributes = True


class PaymentHistoryResponse(BaseModel):
    """User's payment history"""
    user_id: str
    total_payments: int
    total_amount_paid: float
    payments: List[PaymentResponse] = Field(default_factory=list)


# ==================== Coupons ====================

class CreateCouponRequest(BaseModel):
    """Create discount coupon"""
    coupon_code: str = Field(..., min_length=4, max_length=20, description="Unique coupon code")
    discount_type: str = Field(..., pattern="^(percentage|fixed)$", description="Discount type")
    discount_value: Decimal = Field(..., gt=0, description="Discount amount or percentage")

    # Applicability
    applicable_plans: Optional[List[str]] = Field(None, description="Specific plan IDs, None = all plans")
    max_uses: Optional[int] = Field(None, ge=1, description="Maximum number of uses")
    max_uses_per_user: int = Field(default=1, ge=1, description="Max uses per user")

    # Validity
    valid_from: date
    valid_until: date

    # Constraints
    min_purchase_amount: Optional[Decimal] = Field(None, ge=0, description="Minimum purchase amount")

    @validator('discount_value')
    def validate_discount(cls, v, values):
        """Validate discount value based on type"""
        discount_type = values.get('discount_type')
        if discount_type == 'percentage' and v > 100:
            raise ValueError("Percentage discount cannot exceed 100")
        return v


class CouponResponse(BaseModel):
    """Coupon details"""
    coupon_id: str
    coupon_code: str
    discount_type: str
    discount_value: float

    # Usage
    total_uses: int
    max_uses: Optional[int]
    remaining_uses: Optional[int]

    # Validity
    valid_from: date
    valid_until: date
    is_active: bool
    is_valid: bool  # Check current date

    created_at: datetime

    class Config:
        from_attributes = True


class ValidateCouponRequest(BaseModel):
    """Validate coupon for subscription"""
    coupon_code: str
    user_id: str
    plan_id: str
    billing_cycle: str


class ValidateCouponResponse(BaseModel):
    """Coupon validation result"""
    is_valid: bool
    coupon_code: str
    discount_amount: float
    reason: Optional[str] = Field(None, description="Reason if invalid")

    # Calculation
    original_amount: float
    discount: float
    final_amount: float


# ==================== Cancellation ====================

class CancelSubscriptionRequest(BaseModel):
    """Cancel subscription"""
    reason: str = Field(..., min_length=10, max_length=500, description="Cancellation reason")
    cancel_immediately: bool = Field(
        default=False,
        description="Cancel now vs at end of billing period"
    )


class CancelSubscriptionResponse(BaseModel):
    """Cancellation confirmation"""
    subscription_id: str
    status: str  # cancelled
    cancelled_at: datetime
    access_until: date  # Last day of access
    refund_amount: Optional[float] = None
    refund_status: Optional[str] = None


# ==================== Renewal ====================

class RenewSubscriptionRequest(BaseModel):
    """Manually renew subscription"""
    subscription_id: str
    payment_method: Optional[str] = None


class RenewSubscriptionResponse(BaseModel):
    """Renewal confirmation"""
    subscription_id: str
    renewed_at: datetime
    new_end_date: date
    amount_charged: float
    payment_id: str


# ==================== Admin ====================

class SubscriptionStatsResponse(BaseModel):
    """System-wide subscription statistics"""
    total_subscriptions: int
    active_subscriptions: int
    expired_subscriptions: int
    cancelled_subscriptions: int

    # By plan
    subscriptions_by_plan: dict  # {plan_name: count}

    # Revenue
    total_revenue_this_month: float
    total_revenue_all_time: float

    # Trends
    new_subscriptions_this_month: int
    cancellations_this_month: int
    renewal_rate: float  # percentage


class GrantTrialRequest(BaseModel):
    """Grant trial subscription to user"""
    user_id: str
    plan_id: str
    trial_days: int = Field(default=7, ge=1, le=30, description="Trial duration in days")


class GrantTrialResponse(BaseModel):
    """Trial grant confirmation"""
    subscription_id: str
    user_id: str
    plan_name: str
    trial_end_date: date
    status: str


class BulkSubscriptionUpdateRequest(BaseModel):
    """Bulk update subscriptions"""
    subscription_ids: List[str] = Field(..., min_items=1, max_items=100)
    action: str = Field(..., pattern="^(activate|suspend|cancel|extend)$")
    days_to_extend: Optional[int] = Field(None, ge=1, description="Days to extend (for extend action)")


class BulkSubscriptionUpdateResponse(BaseModel):
    """Bulk update result"""
    total_requested: int
    successful: int
    failed: int
    errors: List[dict] = Field(default_factory=list)
