"""
Discount Code Usage Tracking Model

Tracks which users have used which discount codes (for per-user limits).
"""

from sqlalchemy import Column, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import datetime


class DiscountCodeUsage(Base):
    """
    Tracks discount code usage per user.

    Enforces per-user usage limits and provides audit trail.
    """
    __tablename__ = "discount_code_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References
    discount_code_id = Column(UUID(as_uuid=True), ForeignKey("discount_codes.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False)

    # Usage details
    discount_amount_inr = Column(String(20), nullable=False)  # Amount saved
    used_at = Column(String(100), default=lambda: datetime.utcnow().isoformat(), index=True)

    # Relationships
    discount_code = relationship("DiscountCode", backref="usages")
    user = relationship("User", backref="discount_usages")
    payment = relationship("Payment")

    def __repr__(self):
        return f"<DiscountCodeUsage user={self.user_id} code={self.discount_code_id}>"


# Composite index for checking if user has used a specific code
Index('idx_discount_usage_user_code',
      DiscountCodeUsage.user_id,
      DiscountCodeUsage.discount_code_id)
