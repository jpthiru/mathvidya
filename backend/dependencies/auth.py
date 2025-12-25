"""
Authentication Dependencies

FastAPI dependency injection for JWT authentication and role-based access control.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime, timedelta

from config.settings import settings
from database import get_session
from models import User
from models.enums import UserRole


# HTTP Bearer token scheme
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Payload data to encode (should include 'sub' for user_id and 'role')
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token

    Raises:
        HTTPException: If token is invalid or user not found

    Returns:
        User object of the authenticated user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Fetch user from database
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure the user is active

    Raises:
        HTTPException: If user account is inactive

    Returns:
        Active user object
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )

    return current_user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory for role-based access control

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_role(UserRole.ADMIN))):
            ...

    Args:
        allowed_roles: One or more UserRole values that are allowed

    Returns:
        FastAPI dependency function
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        # Convert string role to UserRole enum for comparison
        user_role_str = current_user.role  # This is a string from PgEnum

        # Check if user's role matches any of the allowed roles
        if user_role_str not in [role.value for role in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(r.value for r in allowed_roles)}"
            )

        return current_user

    return role_checker


# Convenience dependencies for common role checks
require_student = require_role(UserRole.STUDENT)
require_teacher = require_role(UserRole.TEACHER)
require_admin = require_role(UserRole.ADMIN)
require_parent = require_role(UserRole.PARENT)

# Allow multiple roles
require_student_or_parent = require_role(UserRole.STUDENT, UserRole.PARENT)
require_teacher_or_admin = require_role(UserRole.TEACHER, UserRole.ADMIN)
