"""
Invoice Model

Generates and stores invoices with GST breakdown.
"""

from sqlalchemy import Column, String, Numeric, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import datetime


class Invoice(Base):
    """
    Tax invoices for subscription payments.

    Generated after successful payment with GST breakdown.
    Immutable record for compliance and customer download.
    """
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Invoice number (sequential, formatted)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)  # INV-FY2425-00001

    # References
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False, unique=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("user_subscriptions.id"))

    # Invoice details
    invoice_date = Column(String(100), nullable=False, default=lambda: datetime.utcnow().isoformat())

    # Customer details (snapshot at time of invoice)
    customer_name = Column(String(200), nullable=False)
    customer_email = Column(String(200), nullable=False)
    customer_phone = Column(String(20))
    customer_address = Column(Text)
    customer_state = Column(String(100))  # For CGST/SGST vs IGST

    # Line item (subscription plan)
    item_description = Column(Text, nullable=False)  # "Premium MCQ - Monthly Subscription"
    item_quantity = Column(String(10), default="1")
    item_unit_price = Column(Numeric(10, 2), nullable=False)  # Base price before GST

    # Amounts
    subtotal_inr = Column(Numeric(10, 2), nullable=False)  # Before GST
    discount_inr = Column(Numeric(10, 2), default=0)  # Discount applied
    taxable_amount_inr = Column(Numeric(10, 2), nullable=False)  # After discount, before GST

    # GST breakdown (Tamil Nadu: CGST 9% + SGST 9%)
    cgst_rate = Column(Numeric(5, 2), default=9.00)  # 9%
    cgst_amount_inr = Column(Numeric(10, 2), default=0)

    sgst_rate = Column(Numeric(5, 2), default=9.00)  # 9%
    sgst_amount_inr = Column(Numeric(10, 2), default=0)

    igst_rate = Column(Numeric(5, 2), default=18.00)  # 18% for inter-state
    igst_amount_inr = Column(Numeric(10, 2), default=0)

    total_gst_inr = Column(Numeric(10, 2), nullable=False)  # Sum of CGST+SGST or IGST

    # Final total
    total_amount_inr = Column(Numeric(10, 2), nullable=False)  # Amount paid (with GST)

    # Company details (seller)
    company_name = Column(String(200), default="Quantvin Technologies")
    company_gst = Column(String(20), default="33ABXPL0022H1ZU")
    company_address = Column(Text)
    company_state = Column(String(100), default="Tamil Nadu")

    # PDF storage (optional - can generate on-the-fly)
    pdf_url = Column(String(500))  # S3 URL if we store PDFs

    # Metadata
    created_at = Column(String(100), default=lambda: datetime.utcnow().isoformat())

    # Relationships
    user = relationship("User", backref="invoices")

    def __repr__(self):
        return f"<Invoice {self.invoice_number} - ₹{self.total_amount_inr}>"


# Index for invoice lookup
Index('idx_invoice_user_date', Invoice.user_id, Invoice.invoice_date.desc())
