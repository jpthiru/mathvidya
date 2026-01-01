"""
Email Verification Model

Stores email verification codes for user registration and password reset.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
import random
import string

from database import Base


class EmailVerification(Base):
    """Email verification code storage"""

    __tablename__ = "email_verifications"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User reference (nullable - code can be created before user exists for registration)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=True)

    # Email and code
    email = Column(String(255), nullable=False, index=True)
    code = Column(String(6), nullable=False)  # 6-digit code

    # Type of verification
    verification_type = Column(String(20), nullable=False, default="registration")  # registration, password_reset

    # Tracking
    attempts = Column(Integer, default=0)  # Wrong attempts count
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)  # When code was successfully verified

    # Indexes
    __table_args__ = (
        Index('ix_email_verifications_email_type', 'email', 'verification_type'),
        Index('ix_email_verifications_code_email', 'code', 'email'),
    )

    @staticmethod
    def generate_code() -> str:
        """Generate a random 6-digit numeric code"""
        return ''.join(random.choices(string.digits, k=6))

    def is_expired(self) -> bool:
        """Check if the verification code has expired"""
        return datetime.now(timezone.utc) > self.expires_at

    def is_valid(self, code: str) -> bool:
        """Check if the provided code matches and is not expired"""
        return self.code == code and not self.is_expired() and self.verified_at is None

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "email": self.email,
            "verification_type": self.verification_type,
            "attempts": self.attempts,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
        }
