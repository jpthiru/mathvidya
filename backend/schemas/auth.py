"""
Authentication Schemas

Pydantic models for authentication request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from models.enums import UserRole


class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    role: UserRole
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    
    # Student-specific fields
    student_class: Optional[str] = Field(None, description="Required for students: X or XII")
    school_name: Optional[str] = Field(None, max_length=255)
    
    @validator('student_class')
    def validate_student_class(cls, v, values):
        """Ensure student_class is provided for students"""
        if values.get('role') == UserRole.STUDENT and not v:
            raise ValueError("student_class is required for student registration")
        if v and v not in ['X', 'XII']:
            raise ValueError("student_class must be 'X' or 'XII'")
        return v

    class Config:
        use_enum_values = True


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User information response"""
    user_id: str
    email: str
    role: str
    first_name: str
    last_name: str
    full_name: str
    phone: Optional[str] = None
    student_class: Optional[str] = None
    is_active: bool
    email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str = Field(..., min_length=8)


class PasswordResetRequest(BaseModel):
    """Password reset request (forgot password)"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token"""
    token: str
    new_password: str = Field(..., min_length=8)
