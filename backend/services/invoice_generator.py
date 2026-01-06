"""
Invoice Generation Service

Generates GST-compliant tax invoices for subscription payments.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Invoice, Payment, User, SubscriptionPlan
from datetime import datetime
from decimal import Decimal
import uuid


class InvoiceGenerator:
    """
    Service for generating GST-compliant invoices.

    Features:
    - Automatic invoice numbering (INV-FY2425-00001)
    - GST calculation (CGST 9% + SGST 9% for Tamil Nadu)
    - IGST calculation (18% for inter-state)
    - Customer details from user profile
    - Company details pre-configured
    """

    # Company details (Quantvin Technologies)
    COMPANY_NAME = "Quantvin Technologies"
    COMPANY_GST = "33ABXPL0022H1ZU"
    COMPANY_ADDRESS = "123 Tech Park, Coimbatore, Tamil Nadu 641001, India"
    COMPANY_STATE = "Tamil Nadu"
    COMPANY_STATE_CODE = "33"  # Tamil Nadu

    # GST rates
    CGST_RATE = Decimal("9.00")  # 9%
    SGST_RATE = Decimal("9.00")  # 9%
    IGST_RATE = Decimal("18.00")  # 18%

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_invoice_number(self) -> str:
        """
        Generate next invoice number in format: INV-FY2425-00001

        Financial year runs Apr-Mar in India, so:
        - Jan-Mar 2025 = FY2425
        - Apr-Dec 2025 = FY2526
        """
        now = datetime.utcnow()

        # Determine financial year
        if now.month >= 4:  # Apr-Dec
            fy_year = f"FY{str(now.year)[-2:]}{str(now.year + 1)[-2:]}"
        else:  # Jan-Mar
            fy_year = f"FY{str(now.year - 1)[-2:]}{str(now.year)[-2:]}"

        # Get last invoice for this FY
        result = await self.db.execute(
            select(Invoice)
            .where(Invoice.invoice_number.like(f"INV-{fy_year}-%"))
            .order_by(Invoice.invoice_number.desc())
            .limit(1)
        )
        last_invoice = result.scalar_one_or_none()

        if last_invoice:
            # Extract sequence number and increment
            last_num = int(last_invoice.invoice_number.split("-")[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"INV-{fy_year}-{next_num:05d}"

    def calculate_gst(
        self,
        taxable_amount: Decimal,
        customer_state: str = "Tamil Nadu"
    ) -> dict:
        """
        Calculate GST breakdown based on customer state.

        Args:
            taxable_amount: Amount before tax
            customer_state: Customer's state for inter-state check

        Returns:
            dict with cgst, sgst, igst, and total_gst
        """
        taxable = Decimal(str(taxable_amount))

        # Intra-state (Tamil Nadu to Tamil Nadu): CGST + SGST
        if customer_state == self.COMPANY_STATE:
            cgst = (taxable * self.CGST_RATE / 100).quantize(Decimal("0.01"))
            sgst = (taxable * self.SGST_RATE / 100).quantize(Decimal("0.01"))
            igst = Decimal("0.00")
            total_gst = cgst + sgst
        else:
            # Inter-state: IGST only
            cgst = Decimal("0.00")
            sgst = Decimal("0.00")
            igst = (taxable * self.IGST_RATE / 100).quantize(Decimal("0.01"))
            total_gst = igst

        return {
            "cgst_rate": self.CGST_RATE if cgst > 0 else Decimal("0.00"),
            "cgst_amount": cgst,
            "sgst_rate": self.SGST_RATE if sgst > 0 else Decimal("0.00"),
            "sgst_amount": sgst,
            "igst_rate": self.IGST_RATE if igst > 0 else Decimal("0.00"),
            "igst_amount": igst,
            "total_gst": total_gst
        }

    async def create_invoice(
        self,
        payment_id: uuid.UUID,
        subscription_id: uuid.UUID = None
    ) -> Invoice:
        """
        Create invoice for a payment.

        Args:
            payment_id: Payment record ID
            subscription_id: Optional subscription ID (if payment created subscription)

        Returns:
            Created Invoice object

        Raises:
            ValueError: If payment not found or already has invoice
        """
        # Get payment details
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        if payment.invoice:
            raise ValueError(f"Payment {payment_id} already has an invoice")

        # Get user details
        result = await self.db.execute(
            select(User).where(User.user_id == payment.user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User {payment.user_id} not found")

        # Get plan details
        result = await self.db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.plan_type == payment.plan_type)
        )
        plan = result.scalar_one_or_none()

        if not plan:
            raise ValueError(f"Plan {payment.plan_type} not found")

        # Calculate amounts
        # payment.amount_inr already includes GST
        # We need to reverse-calculate the base amount
        total_amount = Decimal(str(payment.amount_inr))

        # If discount was applied, base amount is stored in payment
        if payment.base_amount_inr:
            base_amount = Decimal(str(payment.base_amount_inr))
        else:
            # Reverse calculate from total (total = base * 1.18 for 18% GST)
            base_amount = (total_amount / Decimal("1.18")).quantize(Decimal("0.01"))

        # Subtract discount to get taxable amount
        discount = Decimal(str(payment.discount_amount_inr or 0))
        taxable_amount = base_amount - discount

        # Calculate GST
        # For now, assume all customers are from Tamil Nadu (CGST + SGST)
        # TODO: Get actual state from user profile when available
        customer_state = "Tamil Nadu"
        gst_breakdown = self.calculate_gst(taxable_amount, customer_state)

        # Generate invoice number
        invoice_number = await self.generate_invoice_number()

        # Create invoice record
        invoice = Invoice(
            id=uuid.uuid4(),
            invoice_number=invoice_number,
            user_id=payment.user_id,
            payment_id=payment.id,
            subscription_id=subscription_id,
            invoice_date=datetime.utcnow().isoformat(),

            # Customer details
            customer_name=user.full_name or user.email,
            customer_email=user.email,
            customer_phone=None,  # TODO: Add phone to user model
            customer_address=None,  # TODO: Add address to user model
            customer_state=customer_state,

            # Item details
            item_description=f"Mathvidya {plan.plan_name} Subscription (30 days)",
            item_quantity="1",
            item_unit_price=base_amount,

            # Amounts
            subtotal_inr=base_amount,
            discount_inr=discount,
            taxable_amount_inr=taxable_amount,

            # GST breakdown
            cgst_rate=gst_breakdown["cgst_rate"],
            cgst_amount_inr=gst_breakdown["cgst_amount"],
            sgst_rate=gst_breakdown["sgst_rate"],
            sgst_amount_inr=gst_breakdown["sgst_amount"],
            igst_rate=gst_breakdown["igst_rate"],
            igst_amount_inr=gst_breakdown["igst_amount"],
            total_gst_inr=gst_breakdown["total_gst"],

            total_amount_inr=total_amount,

            # Company details
            company_name=self.COMPANY_NAME,
            company_gst=self.COMPANY_GST,
            company_address=self.COMPANY_ADDRESS,
            company_state=self.COMPANY_STATE,

            # PDF will be generated later
            pdf_url=None,

            created_at=datetime.utcnow().isoformat()
        )

        self.db.add(invoice)

        # Commit changes (relationship will be established automatically via payment_id)
        await self.db.commit()
        await self.db.refresh(invoice)

        return invoice

    def generate_invoice_text(self, invoice: Invoice) -> str:
        """
        Generate plain text invoice for email/display.

        Args:
            invoice: Invoice object

        Returns:
            Plain text invoice
        """
        lines = [
            "=" * 70,
            f"TAX INVOICE",
            "=" * 70,
            "",
            f"Invoice Number: {invoice.invoice_number}",
            f"Invoice Date: {invoice.invoice_date[:10]}",
            "",
            "SELLER DETAILS:",
            "-" * 70,
            f"{invoice.company_name}",
            f"GSTIN: {invoice.company_gst}",
            f"{invoice.company_address}",
            f"State: {invoice.company_state} (Code: {self.COMPANY_STATE_CODE})",
            "",
            "BUYER DETAILS:",
            "-" * 70,
            f"{invoice.customer_name}",
            f"Email: {invoice.customer_email}",
            f"State: {invoice.customer_state or 'Tamil Nadu'}",
            "",
            "ITEM DETAILS:",
            "-" * 70,
            f"Description: {invoice.item_description}",
            f"Quantity: {invoice.item_quantity}",
            f"Unit Price: ₹{invoice.item_unit_price:.2f}",
            f"Subtotal: ₹{invoice.subtotal_inr:.2f}",
            ""
        ]

        if invoice.discount_inr > 0:
            lines.append(f"Discount: -₹{invoice.discount_inr:.2f}")
            lines.append("")

        lines.extend([
            f"Taxable Amount: ₹{invoice.taxable_amount_inr:.2f}",
            "",
            "GST BREAKDOWN:",
            "-" * 70
        ])

        if invoice.cgst_amount_inr > 0:
            lines.append(f"CGST ({invoice.cgst_rate}%): ₹{invoice.cgst_amount_inr:.2f}")
            lines.append(f"SGST ({invoice.sgst_rate}%): ₹{invoice.sgst_amount_inr:.2f}")
        else:
            lines.append(f"IGST ({invoice.igst_rate}%): ₹{invoice.igst_amount_inr:.2f}")

        lines.extend([
            f"Total GST: ₹{invoice.total_gst_inr:.2f}",
            "",
            "=" * 70,
            f"TOTAL AMOUNT: ₹{invoice.total_amount_inr:.2f}",
            "=" * 70,
            "",
            "Thank you for your business!",
            "For support: support@mathvidya.com | +91 979 136 8540",
            ""
        ])

        return "\n".join(lines)
