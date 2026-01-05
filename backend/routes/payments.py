"""
Payment Routes - Razorpay Integration

API endpoints for payment processing with Razorpay Standard Checkout.

TODO: Add actual Razorpay credentials (key_id, key_secret) when available.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_session
from models import Payment, User, SubscriptionPlan, Subscription, DiscountCode, DiscountCodeUsage
from dependencies.auth import get_current_active_user
from services.invoice_generator import InvoiceGenerator
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import hmac
import hashlib

# TODO: Import razorpay when credentials are available
# import razorpay

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


# TODO: Replace with actual credentials from environment variables
RAZORPAY_KEY_ID = "rzp_test_XXXXXXXXXX"  # TODO: Get from settings
RAZORPAY_KEY_SECRET = "YOUR_KEY_SECRET"  # TODO: Get from settings


class CreateOrderRequest(BaseModel):
    """Request to create Razorpay order"""
    plan_type: str
    discount_code: Optional[str] = None


class CreateOrderResponse(BaseModel):
    """Response with Razorpay order details"""
    order_id: str
    razorpay_order_id: str
    amount_inr: float
    currency: str
    razorpay_key_id: str

    # Price breakdown
    base_amount_inr: float
    discount_amount_inr: float
    gst_amount_inr: float

    # Metadata for frontend
    plan_name: str
    discount_code_applied: Optional[str] = None


class VerifyPaymentRequest(BaseModel):
    """Request to verify Razorpay payment"""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class VerifyPaymentResponse(BaseModel):
    """Response after payment verification"""
    success: bool
    payment_id: str
    invoice_id: Optional[str] = None
    subscription_id: Optional[str] = None
    message: str


@router.post("/create-order", response_model=CreateOrderResponse)
async def create_razorpay_order(
    request: CreateOrderRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Create Razorpay order for subscription payment.

    Steps:
    1. Validate plan exists and is active
    2. Validate discount code if provided
    3. Calculate final amount with GST
    4. Create Razorpay order
    5. Save payment record with 'created' status

    TODO: Initialize razorpay.Client with actual credentials
    """

    # Get plan details
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.plan_type == request.plan_type)
    )
    plan = result.scalar_one_or_none()

    if not plan or not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {request.plan_type} not found or inactive"
        )

    # Calculate amounts
    base_amount = Decimal(str(plan.price_inr))
    discount_amount = Decimal("0.00")
    discount_code_id = None

    # Validate and apply discount code
    if request.discount_code:
        code = request.discount_code.strip().upper()
        result = await db.execute(
            select(DiscountCode).where(DiscountCode.code == code)
        )
        discount = result.scalar_one_or_none()

        if discount and discount.is_active:
            now = datetime.utcnow().isoformat()
            if now >= discount.valid_from and now <= discount.valid_until:
                # Calculate discount
                if discount.discount_type == "percentage":
                    discount_amount = (base_amount * Decimal(str(discount.discount_value))) / 100
                else:  # fixed
                    discount_amount = Decimal(str(discount.discount_value))

                discount_amount = min(discount_amount, base_amount)
                discount_code_id = discount.id

    # Calculate GST (18% = 9% CGST + 9% SGST for Tamil Nadu)
    taxable_amount = base_amount - discount_amount
    gst_amount = (taxable_amount * Decimal("0.18")).quantize(Decimal("0.01"))
    cgst = (gst_amount / 2).quantize(Decimal("0.01"))
    sgst = cgst

    total_amount = (taxable_amount + gst_amount).quantize(Decimal("0.01"))

    # Convert to paise for Razorpay (INR smallest unit)
    amount_paise = int(total_amount * 100)

    # TODO: Create actual Razorpay order
    # client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    # razorpay_order = client.order.create({
    #     "amount": amount_paise,
    #     "currency": "INR",
    #     "receipt": f"order_{current_user.user_id}_{datetime.utcnow().timestamp()}",
    #     "notes": {
    #         "plan_type": request.plan_type,
    #         "user_id": str(current_user.user_id),
    #         "discount_code": request.discount_code or ""
    #     }
    # })

    # STUB: Generate mock order ID
    razorpay_order_id = f"order_stub_{uuid.uuid4().hex[:10]}"
    razorpay_order_response = {
        "id": razorpay_order_id,
        "amount": amount_paise,
        "currency": "INR",
        "status": "created"
    }

    # Create payment record
    payment = Payment(
        id=uuid.uuid4(),
        user_id=current_user.user_id,
        plan_type=request.plan_type,
        razorpay_order_id=razorpay_order_id,
        amount_inr=total_amount,
        currency="INR",
        status="created",
        base_amount_inr=base_amount,
        gst_amount_inr=gst_amount,
        cgst_inr=cgst,
        sgst_inr=sgst,
        igst_inr=Decimal("0.00"),
        discount_code=request.discount_code,
        discount_amount_inr=discount_amount,
        razorpay_order_response=razorpay_order_response,
        created_at=datetime.utcnow().isoformat()
    )

    db.add(payment)
    await db.commit()

    return CreateOrderResponse(
        order_id=str(payment.id),
        razorpay_order_id=razorpay_order_id,
        amount_inr=float(total_amount),
        currency="INR",
        razorpay_key_id=RAZORPAY_KEY_ID,
        base_amount_inr=float(base_amount),
        discount_amount_inr=float(discount_amount),
        gst_amount_inr=float(gst_amount),
        plan_name=plan.plan_name,
        discount_code_applied=request.discount_code if discount_amount > 0 else None
    )


@router.post("/verify", response_model=VerifyPaymentResponse)
async def verify_payment(
    request: VerifyPaymentRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Verify Razorpay payment signature and activate subscription.

    Steps:
    1. Verify payment signature
    2. Update payment status to 'captured'
    3. Create/extend subscription
    4. Generate invoice
    5. Record discount code usage
    6. Send confirmation email (TODO)

    TODO: Implement actual signature verification with Razorpay secret
    """

    # Get payment record
    result = await db.execute(
        select(Payment).where(
            Payment.razorpay_order_id == request.razorpay_order_id
        )
    )
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    if payment.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized"
        )

    # TODO: Verify signature with actual Razorpay secret
    # generated_signature = hmac.new(
    #     RAZORPAY_KEY_SECRET.encode(),
    #     f"{request.razorpay_order_id}|{request.razorpay_payment_id}".encode(),
    #     hashlib.sha256
    # ).hexdigest()
    #
    # if generated_signature != request.razorpay_signature:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Invalid payment signature"
    #     )

    # STUB: Accept signature for testing
    # In production, uncomment the verification above

    # Update payment status
    payment.razorpay_payment_id = request.razorpay_payment_id
    payment.razorpay_signature = request.razorpay_signature
    payment.status = "captured"
    payment.payment_completed_at = datetime.utcnow().isoformat()

    # Create or extend subscription
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.user_id,
            Subscription.plan_type == payment.plan_type
        )
    )
    subscription = result.scalar_one_or_none()

    now = datetime.utcnow()

    if subscription and subscription.subscription_status == "active":
        # Extend existing subscription by 30 days
        end_date = datetime.fromisoformat(subscription.end_date.replace('Z', '+00:00'))
        new_end_date = end_date + timedelta(days=30)
        subscription.end_date = new_end_date.isoformat()
    else:
        # Create new subscription
        subscription = Subscription(
            subscription_id=uuid.uuid4(),
            user_id=current_user.user_id,
            plan_type=payment.plan_type,
            start_date=now.isoformat(),
            end_date=(now + timedelta(days=30)).isoformat(),
            subscription_status="active",
            is_active=True,
            created_at=now.isoformat()
        )
        db.add(subscription)

    # Generate invoice
    invoice_generator = InvoiceGenerator(db)
    invoice = await invoice_generator.create_invoice(
        payment_id=payment.id,
        subscription_id=subscription.subscription_id
    )

    # Record discount code usage
    if payment.discount_code and payment.discount_amount_inr > 0:
        result = await db.execute(
            select(DiscountCode).where(DiscountCode.code == payment.discount_code.upper())
        )
        discount_code = result.scalar_one_or_none()

        if discount_code:
            usage = DiscountCodeUsage(
                id=uuid.uuid4(),
                discount_code_id=discount_code.id,
                user_id=current_user.user_id,
                payment_id=payment.id,
                discount_amount_inr=str(payment.discount_amount_inr),
                used_at=datetime.utcnow().isoformat()
            )
            db.add(usage)

            # Increment usage count
            discount_code.uses_count += 1

    await db.commit()

    # TODO: Send confirmation email with invoice

    return VerifyPaymentResponse(
        success=True,
        payment_id=str(payment.id),
        invoice_id=str(invoice.id) if invoice else None,
        subscription_id=str(subscription.subscription_id),
        message="Payment verified successfully. Your subscription is now active!"
    )


@router.get("/history")
async def get_payment_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Get payment history for current user.

    Returns all payments with invoice details.
    """
    result = await db.execute(
        select(Payment).where(
            Payment.user_id == current_user.user_id
        ).order_by(Payment.created_at.desc())
    )
    payments = result.scalars().all()

    return [
        {
            "payment_id": str(p.id),
            "plan_type": p.plan_type,
            "amount_inr": float(p.amount_inr),
            "status": p.status,
            "discount_code": p.discount_code,
            "discount_amount_inr": float(p.discount_amount_inr or 0),
            "payment_method": p.payment_method,
            "created_at": p.created_at,
            "payment_completed_at": p.payment_completed_at,
            "invoice_id": str(p.invoice_id) if p.invoice_id else None
        }
        for p in payments
    ]
