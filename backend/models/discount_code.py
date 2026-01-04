"""
Discount Code Model

Manages promotional discount codes with validation rules.
"""

from sqlalchemy import Column, String, Integer, Numeric, Boolean, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import uuid
from datetime import datetime
import enum


class DiscountType(str, enum.Enum):
    """Discount type"""
    PERCENTAGE = "percentage"  # Percentage off (e.g., 20%)
    FIXED = "fixed"  # Fixed amount off (e.g., ₹100)


class DiscountCode(Base):
    """
    Promotional discount codes.

    Supports various validation rules and usage limits.
    Admin creates and manages codes from admin panel.
    """
    __tablename__ = "discount_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Code details
    code = Column(String(50), unique=True, nullable=False, index=True)  # Uppercase alphanumeric
    description = Column(Text)  # Internal notes

    # Discount configuration
    discount_type = Column(String(20), nullable=False, default=DiscountType.PERCENTAGE.value)
    discount_value = Column(Numeric(10, 2), nullable=False)  # Percentage (e.g., 50.00) or Amount (e.g., 100.00)

    # Validity period
    valid_from = Column(String(100), nullable=False, default=lambda: datetime.utcnow().isoformat())
    valid_until = Column(String(100), nullable=False, index=True)

    # Usage limits
    max_uses = Column(Integer)  # Total uses allowed (null = unlimited)
    uses_count = Column(Integer, default=0, nullable=False)  # Times used so far
    max_uses_per_user = Column(Integer, default=1)  # Per-user limit

    # Plan restrictions (null = applies to all plans)
    applicable_plans = Column(Text)  # Comma-separated plan_types: "basic,premium_mcq"

    # Minimum purchase amount (null = no minimum)
    min_purchase_amount = Column(Numeric(10, 2))

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Metadata
    created_by = Column(UUID(as_uuid=True))  # Admin user who created
    created_at = Column(String(100), default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String(100), onupdate=lambda: datetime.utcnow().isoformat())

    def is_valid(self) -> bool:
        """Check if code is currently valid"""
        if not self.is_active:
            return False

        now = datetime.utcnow()
        valid_from = datetime.fromisoformat(self.valid_from)
        valid_until = datetime.fromisoformat(self.valid_until)

        if now < valid_from or now > valid_until:
            return False

        if self.max_uses and self.uses_count >= self.max_uses:
            return False

        return True

    def can_be_used_by_plan(self, plan_type: str) -> bool:
        """Check if code applies to given plan"""
        if not self.applicable_plans:
            return True  # Applies to all plans
        return plan_type in self.applicable_plans.split(',')

    def calculate_discount(self, amount: float) -> float:
        """Calculate discount amount for given price"""
        if self.discount_type == DiscountType.PERCENTAGE.value:
            return float(amount) * (float(self.discount_value) / 100)
        else:  # FIXED
            return float(self.discount_value)

    def increment_usage(self):
        """Increment usage counter"""
        self.uses_count += 1

    def __repr__(self):
        return f"<DiscountCode {self.code} - {self.discount_value}{'%' if self.discount_type == 'percentage' else '₹'}>"


# Index for tracking user-specific code usage (will need separate usage tracking table for this)
Index('idx_discount_code_active_valid', DiscountCode.is_active, DiscountCode.valid_until)
