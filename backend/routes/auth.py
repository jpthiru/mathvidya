"""
Authentication Routes

User registration, login, and authentication endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import bcrypt
from datetime import datetime, timedelta, timezone

from database import get_session
from models import User
from models.enums import UserRole
from schemas.auth import (
    RegisterRequest,
    TokenResponse,
    UserResponse,
    PasswordChangeRequest
)
from dependencies.auth import create_access_token, get_current_active_user
from config.settings import settings


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
