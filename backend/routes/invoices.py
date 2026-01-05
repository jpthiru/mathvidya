"""
Invoice Management Routes

API endpoints for invoice generation and retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_session
from models import Invoice, Payment, User
from services.invoice_generator import InvoiceGenerator
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/v1/invoices", tags=["Invoices"])


class InvoiceResponse(BaseModel):
    """Invoice details response"""
    invoice_id: str
    invoice_number: str
    invoice_date: str

    customer_name: str
    customer_email: str

    item_description: str
    subtotal_inr: float
    discount_inr: float
    taxable_amount_inr: float

    cgst_rate: float
    cgst_amount_inr: float
    sgst_rate: float
    sgst_amount_inr: float
    igst_rate: float
    igst_amount_inr: float

    total_gst_inr: float
    total_amount_inr: float

    company_name: str
    company_gst: str
    company_state: str

    pdf_url: Optional[str] = None


class InvoiceTextResponse(BaseModel):
    """Plain text invoice response"""
    invoice_number: str
    invoice_text: str


@router.post("/generate/{payment_id}", response_model=InvoiceResponse)
async def generate_invoice(
    payment_id: str,
    subscription_id: Optional[str] = None,
    db: AsyncSession = Depends(get_session)
):
    """
    Generate invoice for a payment.

    This endpoint should typically be called automatically after successful payment.
    Manual generation is allowed for admin purposes.

    Args:
        payment_id: Payment UUID
        subscription_id: Optional subscription UUID

    Returns:
        Generated invoice details
    """
    try:
        payment_uuid = uuid.UUID(payment_id)
        subscription_uuid = uuid.UUID(subscription_id) if subscription_id else None
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format"
        )

    generator = InvoiceGenerator(db)

    try:
        invoice = await generator.create_invoice(payment_uuid, subscription_uuid)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return InvoiceResponse(
        invoice_id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        customer_name=invoice.customer_name,
        customer_email=invoice.customer_email,
        item_description=invoice.item_description,
        subtotal_inr=float(invoice.subtotal_inr),
        discount_inr=float(invoice.discount_inr),
        taxable_amount_inr=float(invoice.taxable_amount_inr),
        cgst_rate=float(invoice.cgst_rate),
        cgst_amount_inr=float(invoice.cgst_amount_inr),
        sgst_rate=float(invoice.sgst_rate),
        sgst_amount_inr=float(invoice.sgst_amount_inr),
        igst_rate=float(invoice.igst_rate),
        igst_amount_inr=float(invoice.igst_amount_inr),
        total_gst_inr=float(invoice.total_gst_inr),
        total_amount_inr=float(invoice.total_amount_inr),
        company_name=invoice.company_name,
        company_gst=invoice.company_gst,
        company_state=invoice.company_state,
        pdf_url=invoice.pdf_url
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_session)
):
    """
    Get invoice details by ID.

    TODO: Add authentication and verify user owns this invoice.
    """
    try:
        invoice_uuid = uuid.UUID(invoice_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invoice ID format"
        )

    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_uuid)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    return InvoiceResponse(
        invoice_id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        customer_name=invoice.customer_name,
        customer_email=invoice.customer_email,
        item_description=invoice.item_description,
        subtotal_inr=float(invoice.subtotal_inr),
        discount_inr=float(invoice.discount_inr),
        taxable_amount_inr=float(invoice.taxable_amount_inr),
        cgst_rate=float(invoice.cgst_rate),
        cgst_amount_inr=float(invoice.cgst_amount_inr),
        sgst_rate=float(invoice.sgst_rate),
        sgst_amount_inr=float(invoice.sgst_amount_inr),
        igst_rate=float(invoice.igst_rate),
        igst_amount_inr=float(invoice.igst_amount_inr),
        total_gst_inr=float(invoice.total_gst_inr),
        total_amount_inr=float(invoice.total_amount_inr),
        company_name=invoice.company_name,
        company_gst=invoice.company_gst,
        company_state=invoice.company_state,
        pdf_url=invoice.pdf_url
    )


@router.get("/{invoice_id}/text", response_model=InvoiceTextResponse)
async def get_invoice_text(
    invoice_id: str,
    db: AsyncSession = Depends(get_session)
):
    """
    Get invoice as plain text (for email or display).

    TODO: Add authentication and verify user owns this invoice.
    """
    try:
        invoice_uuid = uuid.UUID(invoice_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invoice ID format"
        )

    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_uuid)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    generator = InvoiceGenerator(db)
    invoice_text = generator.generate_invoice_text(invoice)

    return InvoiceTextResponse(
        invoice_number=invoice.invoice_number,
        invoice_text=invoice_text
    )


@router.get("/user/{user_id}", response_model=list[InvoiceResponse])
async def get_user_invoices(
    user_id: str,
    db: AsyncSession = Depends(get_session)
):
    """
    Get all invoices for a user.

    TODO: Add authentication and verify requesting user is the owner or admin.
    """
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    result = await db.execute(
        select(Invoice)
        .where(Invoice.user_id == user_uuid)
        .order_by(Invoice.invoice_date.desc())
    )
    invoices = result.scalars().all()

    return [
        InvoiceResponse(
            invoice_id=str(inv.id),
            invoice_number=inv.invoice_number,
            invoice_date=inv.invoice_date,
            customer_name=inv.customer_name,
            customer_email=inv.customer_email,
            item_description=inv.item_description,
            subtotal_inr=float(inv.subtotal_inr),
            discount_inr=float(inv.discount_inr),
            taxable_amount_inr=float(inv.taxable_amount_inr),
            cgst_rate=float(inv.cgst_rate),
            cgst_amount_inr=float(inv.cgst_amount_inr),
            sgst_rate=float(inv.sgst_rate),
            sgst_amount_inr=float(inv.sgst_amount_inr),
            igst_rate=float(inv.igst_rate),
            igst_amount_inr=float(inv.igst_amount_inr),
            total_gst_inr=float(inv.total_gst_inr),
            total_amount_inr=float(inv.total_amount_inr),
            company_name=inv.company_name,
            company_gst=inv.company_gst,
            company_state=inv.company_state,
            pdf_url=inv.pdf_url
        )
        for inv in invoices
    ]
