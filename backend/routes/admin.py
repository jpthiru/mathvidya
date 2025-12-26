"""
Admin Routes

Admin-only endpoints for user management and system administration.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
import bcrypt
from datetime import datetime, timezone
import secrets
import string

from database import get_session
from models import User
from models.enums import UserRole
from dependencies.auth import require_admin, get_current_active_user


router = APIRouter()


# ==================== Schemas ====================

class UserListResponse(BaseModel):
    """Response for paginated user list"""
    users: List[dict]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminPasswordResetRequest(BaseModel):
    """Admin request to reset a user's password"""
    new_password: Optional[str] = Field(None, min_length=8, description="New password. If not provided, a random password will be generated.")


class AdminPasswordResetResponse(BaseModel):
    """Response after admin resets a user's password"""
    message: str
    temporary_password: Optional[str] = None


class UserUpdateRequest(BaseModel):
    """Request to update user details"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    student_class: Optional[str] = Field(None, description="X or XII for students")


# ==================== Helper Functions ====================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


def generate_random_password(length: int = 12) -> str:
    """Generate a random password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(characters) for _ in range(length))


# ==================== Endpoints ====================

@router.get("/admin/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role: student, teacher, parent, admin"),
    search: Optional[str] = Query(None, description="Search by email, first name, or last name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    List all users with pagination and filters (Admin only)

    - **page**: Page number (default 1)
    - **page_size**: Number of items per page (default 20, max 100)
    - **role**: Filter by user role
    - **search**: Search in email, first name, or last name
    - **is_active**: Filter by active status
    """

    # Build base query
    query = select(User)
    count_query = select(func.count(User.user_id))

    # Apply filters
    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)

    if search:
        search_pattern = f"%{search}%"
        search_filter = or_(
            User.email.ilike(search_pattern),
            User.first_name.ilike(search_pattern),
            User.last_name.ilike(search_pattern)
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)

    # Get total count
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Calculate pagination
    total_pages = (total + page_size - 1) // page_size
    offset = (page - 1) * page_size

    # Apply pagination and ordering
    query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)

    # Execute query
    result = await session.execute(query)
    users = result.scalars().all()

    return {
        "users": [user.to_dict() for user in users],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/admin/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Get a specific user's details (Admin only)
    """
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user.to_dict()


@router.put("/admin/users/{user_id}")
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Update a user's details (Admin only)
    """
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields if provided
    if request.first_name is not None:
        user.first_name = request.first_name
    if request.last_name is not None:
        user.last_name = request.last_name
    if request.phone is not None:
        user.phone = request.phone
    if request.is_active is not None:
        user.is_active = request.is_active
    if request.student_class is not None and user.role == 'student':
        if request.student_class not in ['X', 'XII']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="student_class must be 'X' or 'XII'"
            )
        user.student_class = request.student_class

    user.updated_at = datetime.now(timezone.utc)
    await session.commit()

    return {"message": "User updated successfully", "user": user.to_dict()}


@router.post("/admin/users/{user_id}/reset-password", response_model=AdminPasswordResetResponse)
async def admin_reset_password(
    user_id: str,
    request: AdminPasswordResetRequest = None,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Reset a user's password (Admin only)

    - If new_password is provided, use that password
    - If not provided, generate a random temporary password

    Returns the temporary password so admin can share it with the user.
    """
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Use provided password or generate a random one
    if request and request.new_password:
        new_password = request.new_password
        temporary_password = None  # Don't return the password if admin set it
    else:
        new_password = generate_random_password()
        temporary_password = new_password  # Return the generated password

    # Hash and update password
    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.now(timezone.utc)

    await session.commit()

    return {
        "message": f"Password reset successfully for {user.email}",
        "temporary_password": temporary_password
    }


@router.post("/admin/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: str,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Toggle a user's active status (Admin only)
    """
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent admin from deactivating themselves
    if str(user.user_id) == str(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )

    # Toggle active status
    user.is_active = not user.is_active
    user.updated_at = datetime.now(timezone.utc)

    await session.commit()

    status_text = "activated" if user.is_active else "deactivated"
    return {"message": f"User {status_text} successfully", "is_active": user.is_active}


@router.get("/admin/stats")
async def get_admin_stats(
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Get system statistics for admin dashboard (Admin only)
    """
    # Total users by role
    result = await session.execute(
        select(User.role, func.count(User.user_id))
        .group_by(User.role)
    )
    role_counts = dict(result.all())

    # Total active users
    active_result = await session.execute(
        select(func.count(User.user_id)).where(User.is_active == True)
    )
    active_users = active_result.scalar()

    # Total users
    total_result = await session.execute(
        select(func.count(User.user_id))
    )
    total_users = total_result.scalar()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "students": role_counts.get('student', 0),
        "teachers": role_counts.get('teacher', 0),
        "parents": role_counts.get('parent', 0),
        "admins": role_counts.get('admin', 0)
    }
