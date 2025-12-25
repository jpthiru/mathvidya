"""
Subscription Models

Subscription plans and user subscriptions with usage tracking.
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, ForeignKey, Text, CheckConstraint, Numeric, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from database import Base
from models.enums import PlanType, SubscriptionStatus

class PgEnum(TypeDecorator):
    """Custom type to handle PostgreSQL ENUMs as strings

    This decorator wraps String columns to properly cast values to PostgreSQL enum types.
    It generates SQL like: CAST(:param AS enum_type_name)
    """
    impl = String
    cache_ok = True

    def __init__(self, enum_type_name, *args, **kwargs):
        self.enum_type_name = enum_type_name
        super().__init__(*args, **kwargs)

    def bind_expression(self, bindvalue):
        #  Use text() to create a custom type reference for casting
        from sqlalchemy import text
        # Create a type clause that can be used in CAST
        from sqlalchemy.dialects.postgresql import ENUM
        # Create an anonymous enum type just for the cast
        enum_type = ENUM(name=self.enum_type_name, create_type=False)
        from sqlalchemy import cast
        return cast(bindvalue, enum_type)

class SubscriptionPlan(Base):
    """Reference data for subscription plan configurations"""

    __tablename__ = "subscription_plans"

    # Primary Key (enum type)
    plan_type = Column(PgEnum('mv_plan_type', 20), primary_key=True)

    # Display
    display_name = Column(String(100), nullable=False)
    description = Column(Text)

    # Limits
    exams_per_month = Column(Integer, nullable=False)
    teacher_hours_per_month = Column(Numeric(5, 2))  # Nullable for some plans

    # Allowed exam types
    allow_board_exam = Column(Boolean, default=True, nullable=False)
    allow_section_practice = Column(Boolean, default=True, nullable=False)
    allow_unit_practice = Column(Boolean, default=False, nullable=False)
    allow_mcq_only = Column(Boolean, default=True, nullable=False)

    # Features
    leaderboard_eligible = Column(Boolean, default=False, nullable=False)
    sla_hours = Column(Integer, nullable=False)  # 24 or 48

    # Pricing (in paise for precision: 99900 paise = INR 999)
    monthly_price_paise = Column(Integer)  # Nullable if not available for monthly
    annual_price_paise = Column(Integer)   # Nullable if not available for annual

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Constraints
    __table_args__ = (
        CheckConstraint('exams_per_month > 0', name='mv_valid_exams_per_month'),
        CheckConstraint('teacher_hours_per_month IS NULL OR teacher_hours_per_month >= 0', name='mv_valid_teacher_hours'),
        CheckConstraint('sla_hours IN (24, 48)', name='mv_valid_sla_hours'),
        CheckConstraint('monthly_price_paise IS NULL OR monthly_price_paise > 0', name='mv_valid_monthly_price'),
        CheckConstraint('annual_price_paise IS NULL OR annual_price_paise > 0', name='mv_valid_annual_price'),
    )

    # Relationships
    # subscriptions = relationship("Subscription", back_populates="plan")

    def __repr__(self):
        return f"<SubscriptionPlan {self.plan_type} - {self.display_name}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "plan_type": self.plan_type,
            "display_name": self.display_name,
            "description": self.description,
            "exams_per_month": self.exams_per_month,
            "teacher_hours_per_month": float(self.teacher_hours_per_month) if self.teacher_hours_per_month else None,
            "allow_board_exam": self.allow_board_exam,
            "allow_section_practice": self.allow_section_practice,
            "allow_unit_practice": self.allow_unit_practice,
            "allow_mcq_only": self.allow_mcq_only,
            "leaderboard_eligible": self.leaderboard_eligible,
            "sla_hours": self.sla_hours,
            "monthly_price_paise": self.monthly_price_paise,
            "annual_price_paise": self.annual_price_paise,
            "is_active": self.is_active,
        }


class Subscription(Base):
    """Student subscriptions with usage tracking and billing cycles"""

    __tablename__ = "subscriptions"

    # Primary Key
    subscription_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    student_user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    plan_type = Column(PgEnum('mv_plan_type', 20), ForeignKey('subscription_plans.plan_type'), nullable=False)

    # Period
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    billing_cycle = Column(String(20), nullable=False)  # 'monthly' or 'annual'

    # Status
    status = Column(PgEnum('mv_subscription_status', 20), default=SubscriptionStatus.ACTIVE, nullable=False, index=True)

    # Monthly usage tracking (reset on billing_day_of_month)
    exams_used_this_month = Column(Integer, default=0, nullable=False)
    exams_limit_per_month = Column(Integer, nullable=False)
    teacher_hours_used = Column(Numeric(5, 2), default=0)
    teacher_hours_limit = Column(Numeric(5, 2))

    # Billing reset tracking
    billing_day_of_month = Column(Integer, nullable=False)  # 1-28
    last_counter_reset_date = Column(Date)

    # Payment
    amount_paid_paise = Column(Integer, nullable=False)
    currency = Column(String(3), default='INR', nullable=False)
    payment_gateway = Column(String(50))  # 'razorpay', 'stripe', etc.
    payment_gateway_ref = Column(String(255))

    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Constraints
    __table_args__ = (
        CheckConstraint('end_date > start_date', name='mv_valid_subscription_dates'),
        CheckConstraint('exams_used_this_month >= 0', name='mv_valid_exams_used'),
        CheckConstraint('teacher_hours_used IS NULL OR teacher_hours_used >= 0', name='mv_valid_hours_used'),
        CheckConstraint('billing_cycle IN (\'monthly\', \'annual\')', name='mv_valid_billing_cycle'),
        CheckConstraint('billing_day_of_month BETWEEN 1 AND 28', name='mv_valid_billing_day'),
        # Note: Exclusion constraint for overlapping active subscriptions will be added in migration
    )

    # Relationships
    # student = relationship("User", back_populates="subscriptions")
    # plan = relationship("SubscriptionPlan", back_populates="subscriptions")

    def __repr__(self):
        return f"<Subscription {self.student_user_id} - {self.plan_type} ({self.status})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "subscription_id": str(self.subscription_id),
            "student_user_id": str(self.student_user_id),
            "plan_type": self.plan_type,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "billing_cycle": self.billing_cycle,
            "status": self.status,
            "exams_used_this_month": self.exams_used_this_month,
            "exams_limit_per_month": self.exams_limit_per_month,
            "teacher_hours_used": float(self.teacher_hours_used) if self.teacher_hours_used else None,
            "teacher_hours_limit": float(self.teacher_hours_limit) if self.teacher_hours_limit else None,
            "billing_day_of_month": self.billing_day_of_month,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def has_exams_remaining(self) -> bool:
        """Check if user has exams remaining this month"""
        return self.exams_used_this_month < self.exams_limit_per_month

    def has_teacher_hours_remaining(self) -> bool:
        """Check if user has teacher hours remaining"""
        if self.teacher_hours_limit is None:
            return True  # Unlimited
        return self.teacher_hours_used < self.teacher_hours_limit
