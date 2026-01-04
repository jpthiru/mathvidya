"""
Promo Code Routes

Endpoints for promotional code management and validation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from database import get_session
from models.promo_code import PromoCode, PromoCodeUsage, PromoType
from models.user import User
from dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/promo", tags=["Promo Codes"])


# ============================================
# Pydantic Schemas
# ============================================

class PromoCodeValidateRequest(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    plan: Optional[str] = None  # Optional plan to check applicability


class PromoCodeValidateResponse(BaseModel):
    valid: bool
    code: str
    promo_type: Optional[str] = None
    discount_display: Optional[str] = None
    description: Optional[str] = None
    message: str


class PromoCodeCreateRequest(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = None
    promo_type: str = PromoType.PERCENTAGE.value
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    discount_amount: Optional[float] = Field(None, ge=0)
    free_days: Optional[int] = Field(None, ge=1)
    free_months: Optional[int] = Field(None, ge=1)
    applicable_plans: Optional[List[str]] = None
    max_uses: Optional[int] = Field(None, ge=1)
    max_uses_per_user: int = Field(1, ge=1)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = True
    new_users_only: bool = False
    minimum_order_value: Optional[float] = None
    notes: Optional[str] = None


class PromoCodeResponse(BaseModel):
    id: str
    code: str
    description: Optional[str]
    promo_type: str
    discount_percentage: Optional[float]
    discount_amount: Optional[float]
    free_days: Optional[int]
    free_months: Optional[int]
    applicable_plans: Optional[List[str]]
    max_uses: Optional[int]
    current_uses: int
    max_uses_per_user: int
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    is_active: bool
    new_users_only: bool
    minimum_order_value: Optional[float]
    discount_display: str
    is_valid: bool
    created_at: datetime


# ============================================
# Public Endpoints
# ============================================

@router.post("/validate", response_model=PromoCodeValidateResponse)
async def validate_promo_code(
    request: PromoCodeValidateRequest,
    db: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Validate a promo code and return discount details.
    Can be called by authenticated or unauthenticated users.
    """
    code_upper = request.code.upper().strip()

    # Find the promo code
    result = await db.execute(
        select(PromoCode).where(PromoCode.code == code_upper)
    )
    promo = result.scalar_one_or_none()

    if not promo:
        return PromoCodeValidateResponse(
            valid=False,
            code=request.code,
            message="Invalid promo code"
        )

    # Check if code is valid
    if not promo.is_valid():
        if not promo.is_active:
            message = "This promo code is no longer active"
        elif promo.valid_until and datetime.now(timezone.utc) > promo.valid_until:
            message = "This promo code has expired"
        elif promo.valid_from and datetime.now(timezone.utc) < promo.valid_from:
            message = "This promo code is not yet active"
        elif promo.max_uses and promo.current_uses >= promo.max_uses:
            message = "This promo code has reached its usage limit"
        else:
            message = "This promo code is not valid"

        return PromoCodeValidateResponse(
            valid=False,
            code=request.code,
            message=message
        )

    # Check plan applicability
    if promo.applicable_plans and request.plan:
        if request.plan not in promo.applicable_plans:
            return PromoCodeValidateResponse(
                valid=False,
                code=request.code,
                message=f"This promo code is not applicable to the {request.plan} plan"
            )

    # Check per-user usage limit
    if current_user and promo.max_uses_per_user:
        result = await db.execute(
            select(PromoCodeUsage).where(
                and_(
                    PromoCodeUsage.promo_code_id == promo.id,
                    PromoCodeUsage.user_id == current_user.user_id
                )
            )
        )
        user_usages = result.scalars().all()
        if len(user_usages) >= promo.max_uses_per_user:
            return PromoCodeValidateResponse(
                valid=False,
                code=request.code,
                message="You have already used this promo code"
            )

    # Check new users only restriction
    if promo.new_users_only and current_user:
        # Check if user has any past subscriptions
        # For now, just check if they have an existing active subscription
        from models.subscription import Subscription
        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == current_user.user_id
            )
        )
        existing_subscriptions = result.scalars().all()
        if existing_subscriptions:
            return PromoCodeValidateResponse(
                valid=False,
                code=request.code,
                message="This promo code is only for new subscribers"
            )

    # Valid code!
    return PromoCodeValidateResponse(
        valid=True,
        code=promo.code,
        promo_type=promo.promo_type,
        discount_display=promo.get_discount_display(),
        description=promo.description,
        message=f"Promo code applied: {promo.get_discount_display()}"
    )


# ============================================
# Admin Endpoints
# ============================================

@router.get("/", response_model=List[PromoCodeResponse])
async def list_promo_codes(
    skip: int = 0,
    limit: int = 50,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin)
):
    """List all promo codes (admin only)"""
    query = select(PromoCode).order_by(PromoCode.created_at.desc())

    if not include_inactive:
        query = query.where(PromoCode.is_active == True)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    promos = result.scalars().all()

    return [
        PromoCodeResponse(
            id=str(p.id),
            code=p.code,
            description=p.description,
            promo_type=p.promo_type,
            discount_percentage=p.discount_percentage,
            discount_amount=p.discount_amount,
            free_days=p.free_days,
            free_months=p.free_months,
            applicable_plans=p.applicable_plans,
            max_uses=p.max_uses,
            current_uses=p.current_uses,
            max_uses_per_user=p.max_uses_per_user,
            valid_from=p.valid_from,
            valid_until=p.valid_until,
            is_active=p.is_active,
            new_users_only=p.new_users_only,
            minimum_order_value=p.minimum_order_value,
            discount_display=p.get_discount_display(),
            is_valid=p.is_valid(),
            created_at=p.created_at
        )
        for p in promos
    ]


@router.post("/", response_model=PromoCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_promo_code(
    request: PromoCodeCreateRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin)
):
    """Create a new promo code (admin only)"""
    code_upper = request.code.upper().strip()

    # Check if code already exists
    result = await db.execute(
        select(PromoCode).where(PromoCode.code == code_upper)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Promo code '{code_upper}' already exists"
        )

    # Validate promo type requirements
    if request.promo_type == PromoType.PERCENTAGE.value:
        if not request.discount_percentage:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Percentage discount requires discount_percentage field"
            )
    elif request.promo_type == PromoType.FIXED_AMOUNT.value:
        if not request.discount_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fixed amount discount requires discount_amount field"
            )
    elif request.promo_type == PromoType.FREE_TRIAL.value:
        if not request.free_days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Free trial requires free_days field"
            )
    elif request.promo_type == PromoType.FREE_SUBSCRIPTION.value:
        if not request.free_months:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Free subscription requires free_months field"
            )

    promo = PromoCode(
        code=code_upper,
        description=request.description,
        promo_type=request.promo_type,
        discount_percentage=request.discount_percentage,
        discount_amount=request.discount_amount,
        free_days=request.free_days,
        free_months=request.free_months,
        applicable_plans=request.applicable_plans,
        max_uses=request.max_uses,
        max_uses_per_user=request.max_uses_per_user,
        valid_from=request.valid_from,
        valid_until=request.valid_until,
        is_active=request.is_active,
        new_users_only=request.new_users_only,
        minimum_order_value=request.minimum_order_value,
        notes=request.notes,
        created_by=current_user.email
    )

    db.add(promo)
    await db.commit()
    await db.refresh(promo)

    return PromoCodeResponse(
        id=str(promo.id),
        code=promo.code,
        description=promo.description,
        promo_type=promo.promo_type,
        discount_percentage=promo.discount_percentage,
        discount_amount=promo.discount_amount,
        free_days=promo.free_days,
        free_months=promo.free_months,
        applicable_plans=promo.applicable_plans,
        max_uses=promo.max_uses,
        current_uses=promo.current_uses,
        max_uses_per_user=promo.max_uses_per_user,
        valid_from=promo.valid_from,
        valid_until=promo.valid_until,
        is_active=promo.is_active,
        new_users_only=promo.new_users_only,
        minimum_order_value=promo.minimum_order_value,
        discount_display=promo.get_discount_display(),
        is_valid=promo.is_valid(),
        created_at=promo.created_at
    )


@router.patch("/{promo_id}/toggle")
async def toggle_promo_code(
    promo_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin)
):
    """Toggle a promo code active/inactive (admin only)"""
    result = await db.execute(
        select(PromoCode).where(PromoCode.id == uuid.UUID(promo_id))
    )
    promo = result.scalar_one_or_none()

    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promo code not found"
        )

    promo.is_active = not promo.is_active
    await db.commit()

    return {
        "success": True,
        "code": promo.code,
        "is_active": promo.is_active,
        "message": f"Promo code {'activated' if promo.is_active else 'deactivated'}"
    }


@router.delete("/{promo_id}")
async def delete_promo_code(
    promo_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin)
):
    """Delete a promo code (admin only)"""
    result = await db.execute(
        select(PromoCode).where(PromoCode.id == uuid.UUID(promo_id))
    )
    promo = result.scalar_one_or_none()

    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promo code not found"
        )

    await db.delete(promo)
    await db.commit()

    return {
        "success": True,
        "message": f"Promo code '{promo.code}' deleted"
    }
