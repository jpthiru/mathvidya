"""
User Schemas

Pydantic models for request/response validation.
"""

from pydantic import BaseModel, EmailStr, UUID4, Field, validator
from typing import Optional
from datetime import datetime
from models.user import UserRole


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole
    student_class: Optional[str] = Field(None, regex=r'^(X|XII)$')

    @validator('student_class')
    def validate_student_class(cls, v, values):
        """Validate student_class is provided for student role"""
        if values.get('role') == UserRole.STUDENT and not v:
            raise ValueError('student_class is required for students')
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response (no password)"""
    user_id: UUID4
    role: UserRole
    student_class: Optional[str]
    is_active: bool
    email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2


class TokenResponse(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    student_photo_url: Optional[str] = None
    school_name: Optional[str] = Field(None, max_length=255)


class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @validator('new_password')
    def passwords_different(cls, v, values):
        """Ensure new password is different from current"""
        if 'current_password' in values and v == values['current_password']:
            raise ValueError('New password must be different from current password')
        return v
