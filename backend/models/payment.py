"""
Payment Model

Records all payment transactions with Razorpay integration data.
"""

from sqlalchemy import Column, String, Integer, Numeric, Text, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import datetime
import enum


class PaymentStatus(str, enum.Enum):
    """Payment status types"""
    CREATED = "created"  # Order created, payment pending
    PENDING = "pending"  # Payment initiated
    AUTHORIZED = "authorized"  # Payment authorized but not captured
    CAPTURED = "captured"  # Payment successful
    FAILED = "failed"  # Payment failed
    REFUNDED = "refunded"  # Payment refunded


class PaymentMethod(str, enum.Enum):
    """Payment method types"""
    CARD = "card"
    UPI = "upi"
    NETBANKING = "netbanking"
    WALLET = "wallet"
    EMI = "emi"


class Payment(Base):
    """
    Payment transaction records.

    Stores complete Razorpay payment data including webhooks.
    Immutable audit trail of all payment attempts.
    """
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User reference
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # Plan reference (plan_type is the primary key in subscription_plans table)
    plan_type = Column(String(20), ForeignKey("subscription_plans.plan_type"), nullable=False)

    # Razorpay IDs
    razorpay_order_id = Column(String(100), unique=True, index=True)  # order_xxx
    razorpay_payment_id = Column(String(100), unique=True, index=True)  # pay_xxx
    razorpay_signature = Column(String(200))  # Signature for verification

    # Payment details
    amount_inr = Column(Numeric(10, 2), nullable=False)  # Amount charged (with GST)
    currency = Column(String(3), default="INR", nullable=False)
    status = Column(String(20), nullable=False, default=PaymentStatus.CREATED.value, index=True)

    # Payment method (captured from webhook)
    payment_method = Column(String(50))  # card, upi, netbanking, wallet
    payment_method_details = Column(JSON)  # Bank name, card type, UPI ID, etc.

    # Discount tracking
    discount_code = Column(String(50), index=True)
    discount_amount_inr = Column(Numeric(10, 2), default=0)

    # GST breakdown (calculated at payment time)
    base_amount_inr = Column(Numeric(10, 2))  # Amount before GST
    gst_amount_inr = Column(Numeric(10, 2))  # Total GST (CGST + SGST or IGST)
    cgst_inr = Column(Numeric(10, 2))  # Central GST (9%)
    sgst_inr = Column(Numeric(10, 2))  # State GST (9%)
    igst_inr = Column(Numeric(10, 2))  # Integrated GST (18% for inter-state)

    # Invoice reference
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), index=True)

    # Refund tracking
    is_refunded = Column(String(10), default="false")  # "true"/"false" as string for consistency
    refund_amount_inr = Column(Numeric(10, 2), default=0)
    refund_reason = Column(Text)
    refunded_at = Column(String(100))

    # Complete Razorpay response (for debugging and reconciliation)
    razorpay_order_response = Column(JSON)  # Full order creation response
    razorpay_payment_response = Column(JSON)  # Full payment capture response
    razorpay_webhook_data = Column(JSON)  # Webhook payload

    # Metadata
    created_at = Column(String(100), default=lambda: datetime.utcnow().isoformat(), index=True)
    updated_at = Column(String(100), onupdate=lambda: datetime.utcnow().isoformat())
    payment_completed_at = Column(String(100))  # When status became CAPTURED

    # IP and user agent (for fraud detection)
    user_ip = Column(String(50))
    user_agent = Column(String(500))

    # Relationships
    user = relationship("User", backref="payments")
    plan = relationship("SubscriptionPlan", foreign_keys=[plan_type])
    invoice = relationship("Invoice", backref="payment", uselist=False)

    def is_successful(self) -> bool:
        """Check if payment was successful"""
        return self.status == PaymentStatus.CAPTURED.value

    def __repr__(self):
        return f"<Payment {self.razorpay_payment_id} - ₹{self.amount_inr} - {self.status}>"


# Indexes for common queries
Index('idx_payment_user_status', Payment.user_id, Payment.status)
Index('idx_payment_created_at', Payment.created_at.desc())
