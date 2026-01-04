"""
Promo Code Model

Promotional codes for discounts and free trial periods.
Supports:
- Percentage discounts (10%, 20%, etc.)
- Fixed amount discounts (Rs. 100 off, etc.)
- Free trial periods (14 days, 30 days, etc.)
- Usage limits and expiration dates
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime, timezone
import uuid
import enum

from database import Base


class PromoType(str, enum.Enum):
    """Types of promotional codes"""
    PERCENTAGE = "percentage"  # e.g., 20% off
    FIXED_AMOUNT = "fixed_amount"  # e.g., Rs. 500 off
    FREE_TRIAL = "free_trial"  # Free trial period in days
    FREE_SUBSCRIPTION = "free_subscription"  # Free subscription for X months


class PromoCode(Base):
    """
    Promotional codes for discounts and free trials.
    """

    __tablename__ = "promo_codes"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Code details
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    promo_type = Column(String(30), default=PromoType.PERCENTAGE.value, nullable=False)

    # Discount values
    discount_percentage = Column(Float, nullable=True)  # For PERCENTAGE type (0-100)
    discount_amount = Column(Float, nullable=True)  # For FIXED_AMOUNT type (in INR)
    free_days = Column(Integer, nullable=True)  # For FREE_TRIAL type
    free_months = Column(Integer, nullable=True)  # For FREE_SUBSCRIPTION type

    # Applicable plans (null = all plans)
    applicable_plans = Column(ARRAY(String), nullable=True)  # ['basic', 'premium', 'centum']

    # Usage limits
    max_uses = Column(Integer, nullable=True)  # null = unlimited
    current_uses = Column(Integer, default=0, nullable=False)
    max_uses_per_user = Column(Integer, default=1)  # How many times a single user can use this code

    # Validity
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Restrictions
    new_users_only = Column(Boolean, default=False)  # Only for first-time subscribers
    minimum_order_value = Column(Float, nullable=True)  # Minimum subscription value to apply code

    # Metadata
    created_by = Column(String(255), nullable=True)  # Admin who created this code
    notes = Column(Text, nullable=True)  # Internal notes

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<PromoCode {self.code}>"

    def is_valid(self) -> bool:
        """Check if the promo code is currently valid"""
        if not self.is_active:
            return False

        now = datetime.now(timezone.utc)

        if self.valid_from and now < self.valid_from:
            return False

        if self.valid_until and now > self.valid_until:
            return False

        if self.max_uses and self.current_uses >= self.max_uses:
            return False

        return True

    def get_discount_display(self) -> str:
        """Get human-readable discount description"""
        if self.promo_type == PromoType.PERCENTAGE.value:
            return f"{int(self.discount_percentage)}% off"
        elif self.promo_type == PromoType.FIXED_AMOUNT.value:
            return f"₹{int(self.discount_amount)} off"
        elif self.promo_type == PromoType.FREE_TRIAL.value:
            return f"{self.free_days} days free trial"
        elif self.promo_type == PromoType.FREE_SUBSCRIPTION.value:
            months = "month" if self.free_months == 1 else "months"
            return f"{self.free_months} {months} free"
        return "Special offer"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "code": self.code,
            "description": self.description,
            "promo_type": self.promo_type,
            "discount_percentage": self.discount_percentage,
            "discount_amount": self.discount_amount,
            "free_days": self.free_days,
            "free_months": self.free_months,
            "applicable_plans": self.applicable_plans,
            "max_uses": self.max_uses,
            "current_uses": self.current_uses,
            "max_uses_per_user": self.max_uses_per_user,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "is_active": self.is_active,
            "new_users_only": self.new_users_only,
            "minimum_order_value": self.minimum_order_value,
            "discount_display": self.get_discount_display(),
            "is_valid": self.is_valid(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_public_dict(self):
        """Minimal info for public display"""
        return {
            "code": self.code,
            "description": self.description,
            "promo_type": self.promo_type,
            "discount_display": self.get_discount_display(),
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "is_valid": self.is_valid(),
        }


class PromoCodeUsage(Base):
    """
    Track usage of promo codes by users.
    """

    __tablename__ = "promo_code_usages"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References
    promo_code_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    subscription_id = Column(UUID(as_uuid=True), nullable=True)  # If linked to a subscription

    # Applied discount details
    original_amount = Column(Float, nullable=True)
    discount_applied = Column(Float, nullable=True)
    final_amount = Column(Float, nullable=True)

    # Timestamps
    used_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<PromoCodeUsage {self.promo_code_id} by {self.user_id}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "promo_code_id": str(self.promo_code_id),
            "user_id": str(self.user_id),
            "subscription_id": str(self.subscription_id) if self.subscription_id else None,
            "original_amount": self.original_amount,
            "discount_applied": self.discount_applied,
            "final_amount": self.final_amount,
            "used_at": self.used_at.isoformat() if self.used_at else None,
        }
