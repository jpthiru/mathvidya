"""
Discount Code Validation Routes

Provides API endpoints for validating and applying discount codes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from database import get_session
from models import DiscountCode, DiscountCodeUsage, SubscriptionPlan
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/v1/discount-codes", tags=["Discount Codes"])


class ValidateDiscountRequest(BaseModel):
    """Request to validate a discount code"""
    code: str = Field(..., min_length=1, max_length=50, description="Discount code to validate")
    plan_type: str = Field(..., description="Plan type (basic, premium_mcq, premium, centum)")
    user_id: Optional[str] = Field(None, description="User ID if logged in (for per-user limit check)")


class ValidateDiscountResponse(BaseModel):
    """Response with discount validation result"""
    valid: bool
    message: str
    discount_code_id: Optional[str] = None
    discount_type: Optional[str] = None  # percentage or fixed
    discount_value: Optional[float] = None
    applicable_plans: Optional[list[str]] = None

    # Calculated amounts (if valid)
    original_price: Optional[float] = None
    discount_amount: Optional[float] = None
    final_price: Optional[float] = None


@router.post("/validate", response_model=ValidateDiscountResponse)
async def validate_discount_code(
    request: ValidateDiscountRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Validate a discount code and calculate final price.

    Checks:
    1. Code exists and is active
    2. Code is within valid date range
    3. Code hasn't exceeded max uses
    4. Code is applicable to the selected plan
    5. User hasn't exceeded per-user limit (if user_id provided)

    Returns discount calculation if valid.
    """

    # Normalize code to uppercase
    code = request.code.strip().upper()

    # Find discount code
    result = await db.execute(
        select(DiscountCode).where(
            and_(
                DiscountCode.code == code,
                DiscountCode.is_active == True
            )
        )
    )
    discount_code = result.scalar_one_or_none()

    if not discount_code:
        return ValidateDiscountResponse(
            valid=False,
            message="Invalid or inactive discount code"
        )

    # Check date validity
    now = datetime.utcnow().isoformat()
    if now < discount_code.valid_from:
        return ValidateDiscountResponse(
            valid=False,
            message="This discount code is not yet active"
        )

    if now > discount_code.valid_until:
        return ValidateDiscountResponse(
            valid=False,
            message="This discount code has expired"
        )

    # Check max uses
    if discount_code.max_uses is not None and discount_code.uses_count >= discount_code.max_uses:
        return ValidateDiscountResponse(
            valid=False,
            message="This discount code has reached its usage limit"
        )

    # Check plan applicability
    if discount_code.applicable_plans:
        applicable_plans = [p.strip() for p in discount_code.applicable_plans.split(",")]
        if request.plan_type not in applicable_plans:
            return ValidateDiscountResponse(
                valid=False,
                message=f"This discount code is not applicable to the {request.plan_type} plan"
            )
    else:
        applicable_plans = ["basic", "premium_mcq", "premium", "centum"]

    # Check per-user limit (if user is logged in)
    if request.user_id and discount_code.max_uses_per_user:
        try:
            user_uuid = uuid.UUID(request.user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )

        usage_count_result = await db.execute(
            select(DiscountCodeUsage).where(
                and_(
                    DiscountCodeUsage.discount_code_id == discount_code.id,
                    DiscountCodeUsage.user_id == user_uuid
                )
            )
        )
        user_usage_count = len(usage_count_result.scalars().all())

        if user_usage_count >= discount_code.max_uses_per_user:
            return ValidateDiscountResponse(
                valid=False,
                message="You have already used this discount code the maximum number of times"
            )

    # Get plan price
    plan_result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.plan_type == request.plan_type)
    )
    plan = plan_result.scalar_one_or_none()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {request.plan_type} not found"
        )

    original_price = float(plan.price_inr)

    # Calculate discount
    if discount_code.discount_type == "percentage":
        discount_amount = (original_price * float(discount_code.discount_value)) / 100
    else:  # fixed
        discount_amount = float(discount_code.discount_value)

    # Ensure discount doesn't exceed price
    discount_amount = min(discount_amount, original_price)
    final_price = max(0, original_price - discount_amount)

    # Check minimum purchase amount
    if discount_code.min_purchase_amount and original_price < float(discount_code.min_purchase_amount):
        return ValidateDiscountResponse(
            valid=False,
            message=f"Minimum purchase amount of ₹{discount_code.min_purchase_amount} required for this code"
        )

    return ValidateDiscountResponse(
        valid=True,
        message="Discount code applied successfully",
        discount_code_id=str(discount_code.id),
        discount_type=discount_code.discount_type,
        discount_value=float(discount_code.discount_value),
        applicable_plans=applicable_plans,
        original_price=original_price,
        discount_amount=round(discount_amount, 2),
        final_price=round(final_price, 2)
    )
