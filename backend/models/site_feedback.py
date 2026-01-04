"""
Site Feedback Model

General website feedback from users (not exam-specific feedback).
Captures user ratings, suggestions, bug reports, etc.
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
import enum

from database import Base


class FeedbackCategory(str, enum.Enum):
    """Categories of site feedback"""
    SUGGESTION = "suggestion"
    BUG = "bug"
    COMPLIMENT = "compliment"
    QUESTION = "question"
    OTHER = "other"


class FeedbackStatus(str, enum.Enum):
    """Status of feedback"""
    NEW = "new"
    REVIEWED = "reviewed"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SiteFeedback(Base):
    """
    General website/app feedback from users.
    """

    __tablename__ = "site_feedbacks"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User reference (optional - can be from anonymous visitors)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    email = Column(String(255), nullable=True)

    # Feedback details
    rating = Column(Integer, nullable=True)  # 1-5 star rating
    category = Column(String(30), default=FeedbackCategory.OTHER.value, nullable=False)
    message = Column(Text, nullable=False)

    # Context
    page_url = Column(String(500), nullable=True)  # Where was the feedback submitted from
    user_agent = Column(String(500), nullable=True)  # Browser/device info
    ip_address = Column(String(50), nullable=True)

    # Admin handling
    status = Column(String(30), default=FeedbackStatus.NEW.value, nullable=False)
    admin_notes = Column(Text, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<SiteFeedback {self.id} ({self.category})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "email": self.email,
            "rating": self.rating,
            "category": self.category,
            "message": self.message,
            "page_url": self.page_url,
            "status": self.status,
            "admin_notes": self.admin_notes,
            "reviewed_by": str(self.reviewed_by) if self.reviewed_by else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
