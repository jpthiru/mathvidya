"""
Authentication Routes

User registration, login, and authentication endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import bcrypt
from datetime import datetime, timedelta, timezone
import logging

from database import get_session
from models import User, EmailVerification
from models.enums import UserRole
from schemas.auth import (
    RegisterRequest,
    TokenResponse,
    UserResponse,
    PasswordChangeRequest,
    SendVerificationRequest,
    VerifyEmailRequest,
    ResendVerificationRequest,
    VerificationResponse,
    RegisterWithVerificationRequest,
    ResetPasswordRequest,
)
from dependencies.auth import create_access_token, get_current_active_user
from config.settings import settings
from services.email_service import email_service

logger = logging.getLogger(__name__)


router = APIRouter()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


@router.post("/auth/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Register a new user
    
    - **email**: Valid email address (unique)
    - **password**: Minimum 8 characters
    - **role**: student, parent, teacher, or admin
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **student_class**: Required for students (X or XII)
    """
    
    # Check if email already exists
    result = await session.execute(
        select(User).where(User.email == request.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = hash_password(request.password)

    # Get role value (handle both enum and string)
    role_value = request.role.value if hasattr(request.role, 'value') else str(request.role)
    is_student = role_value == 'student' or request.role == UserRole.STUDENT

    # Create new user
    new_user = User(
        email=request.email,
        password_hash=password_hash,
        role=role_value,
        first_name=request.first_name,
        last_name=request.last_name,
        phone=request.phone,
        student_class=request.student_class if is_student else None,
        school_name=request.school_name if is_student else None,
    )
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    return new_user.to_dict()


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session)
):
    """
    Authenticate user and return JWT access token

    Uses OAuth2 password flow (form data):
    - **username**: User's email address
    - **password**: User's password

    Returns JWT token valid for 24 hours
    """

    # Find user by email (OAuth2 uses 'username' field for email)
    result = await session.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()

    # Verify credentials
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.user_id), "role": user.role},
        expires_delta=access_token_expires
    )
    
    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    await session.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user's information
    
    Requires valid JWT token in Authorization header
    """
    return current_user.to_dict()


@router.post("/auth/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Change current user's password
    
    Requires valid JWT token and current password verification
    """
    
    # Verify current password
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Hash and update new password
    current_user.password_hash = hash_password(request.new_password)
    current_user.updated_at = datetime.now(timezone.utc)
    
    await session.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/auth/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout endpoint

    Note: With JWT, actual logout happens client-side by removing the token.
    This endpoint is provided for consistency and can be extended to add
    token blacklisting if needed.
    """
    return {"message": "Logged out successfully"}


# ============================================
# Email Verification Endpoints
# ============================================

@router.post("/auth/send-verification", response_model=VerificationResponse)
async def send_verification_code(
    request: SendVerificationRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Send a 6-digit verification code to the email address.

    Used during registration to verify email ownership before creating account.
    Code expires in 15 minutes.
    """
    # Check if email is already registered
    result = await session.execute(
        select(User).where(User.email == request.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check for recent verification attempts (rate limiting)
    five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
    result = await session.execute(
        select(EmailVerification).where(
            and_(
                EmailVerification.email == request.email,
                EmailVerification.verification_type == request.verification_type,
                EmailVerification.created_at > five_minutes_ago
            )
        )
    )
    recent_verification = result.scalar_one_or_none()

    if recent_verification:
        # Calculate remaining cooldown
        time_since_created = datetime.now(timezone.utc) - recent_verification.created_at.replace(tzinfo=timezone.utc)
        remaining_seconds = 300 - time_since_created.total_seconds()  # 5 minutes = 300 seconds
        if remaining_seconds > 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {int(remaining_seconds)} seconds before requesting a new code"
            )

    # Generate new verification code
    code = EmailVerification.generate_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES)

    # Create verification record
    verification = EmailVerification(
        email=request.email,
        code=code,
        verification_type=request.verification_type,
        expires_at=expires_at,
    )

    session.add(verification)
    await session.commit()

    # Send verification email
    email_sent = email_service.send_verification_email(
        to_email=request.email,
        code=code,
        first_name=request.first_name
    )

    if not email_sent:
        logger.error(f"Failed to send verification email to {request.email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later."
        )

    logger.info(f"Verification code sent to {request.email}")

    return VerificationResponse(
        success=True,
        message="Verification code sent to your email",
        expires_in_minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES
    )


@router.post("/auth/verify-email", response_model=VerificationResponse)
async def verify_email(
    request: VerifyEmailRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Verify email with the 6-digit code.

    Returns success if code is valid and not expired.
    """
    # Find the latest verification for this email
    result = await session.execute(
        select(EmailVerification).where(
            and_(
                EmailVerification.email == request.email,
                EmailVerification.verification_type == "registration",
                EmailVerification.verified_at.is_(None)
            )
        ).order_by(EmailVerification.created_at.desc())
    )
    verification = result.scalar_one_or_none()

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending verification found for this email"
        )

    # Check attempts
    if verification.attempts >= settings.EMAIL_VERIFICATION_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many failed attempts. Please request a new code."
        )

    # Check expiration
    if verification.is_expired():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please request a new code."
        )

    # Verify code
    if verification.code != request.code:
        verification.attempts += 1
        await session.commit()

        remaining_attempts = settings.EMAIL_VERIFICATION_MAX_ATTEMPTS - verification.attempts
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid verification code. {remaining_attempts} attempts remaining."
        )

    # Mark as verified
    verification.verified_at = datetime.now(timezone.utc)
    await session.commit()

    logger.info(f"Email verified successfully: {request.email}")

    return VerificationResponse(
        success=True,
        message="Email verified successfully"
    )


@router.post("/auth/resend-verification", response_model=VerificationResponse)
async def resend_verification_code(
    request: ResendVerificationRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Resend verification code to the email.

    Rate limited to prevent abuse (1 request per 5 minutes).
    """
    # Check for rate limiting - same logic as send-verification
    five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
    result = await session.execute(
        select(EmailVerification).where(
            and_(
                EmailVerification.email == request.email,
                EmailVerification.verification_type == request.verification_type,
                EmailVerification.created_at > five_minutes_ago
            )
        )
    )
    recent_verification = result.scalar_one_or_none()

    if recent_verification:
        time_since_created = datetime.now(timezone.utc) - recent_verification.created_at.replace(tzinfo=timezone.utc)
        remaining_seconds = 300 - time_since_created.total_seconds()
        if remaining_seconds > 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {int(remaining_seconds)} seconds before requesting a new code"
            )

    # Generate new code
    code = EmailVerification.generate_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES)

    # Create new verification record
    verification = EmailVerification(
        email=request.email,
        code=code,
        verification_type=request.verification_type,
        expires_at=expires_at,
    )

    session.add(verification)
    await session.commit()

    # We need the first_name for the email - use a generic greeting
    email_sent = email_service.send_verification_email(
        to_email=request.email,
        code=code,
        first_name="User"  # Generic since we don't have first name for resend
    )

    if not email_sent:
        logger.error(f"Failed to resend verification email to {request.email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later."
        )

    return VerificationResponse(
        success=True,
        message="New verification code sent to your email",
        expires_in_minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES
    )


@router.post("/auth/register-verified", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register_with_verification(
    request: RegisterWithVerificationRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Register a new user with verified email.

    Requires a valid verification code that was previously verified.
    This is the preferred registration endpoint that ensures email ownership.
    """
    # Check if email already exists
    result = await session.execute(
        select(User).where(User.email == request.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Find verified verification record
    result = await session.execute(
        select(EmailVerification).where(
            and_(
                EmailVerification.email == request.email,
                EmailVerification.verification_type == "registration",
                EmailVerification.verified_at.is_not(None)
            )
        ).order_by(EmailVerification.verified_at.desc())
    )
    verification = result.scalar_one_or_none()

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified. Please verify your email first."
        )

    # Check if verification is still within a reasonable time (e.g., 30 minutes)
    verified_time = verification.verified_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - verified_time > timedelta(minutes=30):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification expired. Please verify your email again."
        )

    # Hash password
    password_hash = hash_password(request.password)

    # Get role value
    role_value = request.role.value if hasattr(request.role, 'value') else str(request.role)
    is_student = role_value == 'student' or request.role == UserRole.STUDENT

    # Create new user with email_verified=True
    new_user = User(
        email=request.email,
        password_hash=password_hash,
        role=role_value,
        first_name=request.first_name,
        last_name=request.last_name,
        phone=request.phone,
        student_class=request.student_class if is_student else None,
        school_name=request.school_name if is_student else None,
        email_verified=True,  # Email is verified
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    logger.info(f"New user registered with verified email: {request.email}")

    return new_user.to_dict()


@router.post("/auth/forgot-password", response_model=VerificationResponse)
async def forgot_password(
    request: ResendVerificationRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Send password reset code to registered email.

    For password reset flow - sends a 6-digit code to the user's email.
    """
    # Check if user exists
    result = await session.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        # Don't reveal if email exists or not (security)
        return VerificationResponse(
            success=True,
            message="If the email is registered, you will receive a password reset code.",
            expires_in_minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES
        )

    # Rate limiting
    five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
    result = await session.execute(
        select(EmailVerification).where(
            and_(
                EmailVerification.email == request.email,
                EmailVerification.verification_type == "password_reset",
                EmailVerification.created_at > five_minutes_ago
            )
        )
    )
    recent_verification = result.scalar_one_or_none()

    if recent_verification:
        time_since_created = datetime.now(timezone.utc) - recent_verification.created_at.replace(tzinfo=timezone.utc)
        remaining_seconds = 300 - time_since_created.total_seconds()
        if remaining_seconds > 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {int(remaining_seconds)} seconds before requesting a new code"
            )

    # Generate code
    code = EmailVerification.generate_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES)

    # Create verification record
    verification = EmailVerification(
        email=request.email,
        user_id=user.user_id,
        code=code,
        verification_type="password_reset",
        expires_at=expires_at,
    )

    session.add(verification)
    await session.commit()

    # Send password reset email
    email_sent = email_service.send_password_reset_email(
        to_email=request.email,
        code=code,
        first_name=user.first_name
    )

    if not email_sent:
        logger.error(f"Failed to send password reset email to {request.email}")
        # Still return success to not reveal email existence
        return VerificationResponse(
            success=True,
            message="If the email is registered, you will receive a password reset code.",
            expires_in_minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES
        )

    return VerificationResponse(
        success=True,
        message="If the email is registered, you will receive a password reset code.",
        expires_in_minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES
    )


@router.post("/auth/reset-password", response_model=VerificationResponse)
async def reset_password(
    request: ResetPasswordRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Reset password using verification code.

    Verifies the code and updates the user's password.
    """
    # Find verification
    result = await session.execute(
        select(EmailVerification).where(
            and_(
                EmailVerification.email == request.email,
                EmailVerification.verification_type == "password_reset",
                EmailVerification.verified_at.is_(None)
            )
        ).order_by(EmailVerification.created_at.desc())
    )
    verification = result.scalar_one_or_none()

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No password reset request found for this email"
        )

    # Check attempts
    if verification.attempts >= settings.EMAIL_VERIFICATION_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many failed attempts. Please request a new code."
        )

    # Check expiration
    if verification.is_expired():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code has expired. Please request a new code."
        )

    # Verify code
    if verification.code != request.code:
        verification.attempts += 1
        await session.commit()

        remaining_attempts = settings.EMAIL_VERIFICATION_MAX_ATTEMPTS - verification.attempts
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid code. {remaining_attempts} attempts remaining."
        )

    # Mark as verified
    verification.verified_at = datetime.now(timezone.utc)

    # Update user password
    result = await session.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )

    user.password_hash = hash_password(request.new_password)
    user.updated_at = datetime.now(timezone.utc)

    await session.commit()

    logger.info(f"Password reset successfully for {request.email}")

    return VerificationResponse(
        success=True,
        message="Password reset successfully. You can now log in with your new password."
    )
