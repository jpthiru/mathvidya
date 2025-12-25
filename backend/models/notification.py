"""
Notification Models

Models for notification system:
- Notification: In-app notifications, emails, SMS, push notifications
- NotificationPreference: User preferences for notification channels
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from database import Base


class PgEnum(TypeDecorator):
    """Custom type to handle PostgreSQL ENUMs as strings"""
    impl = String
    cache_ok = True

    def __init__(self, enum_type_name, *args, **kwargs):
        self.enum_type_name = enum_type_name
        super().__init__(*args, **kwargs)

    def bind_expression(self, bindvalue):
        from sqlalchemy import text
        from sqlalchemy.dialects.postgresql import ENUM
        enum_type = ENUM(name=self.enum_type_name, create_type=False)
        from sqlalchemy import cast
        return cast(bindvalue, enum_type)


class Notification(Base):
    """Notifications sent to users via multiple channels"""

    __tablename__ = "notifications"

    # Primary Key
    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Target user
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False, index=True)

    # Classification
    category = Column(PgEnum('mv_notification_category', 50), nullable=False, index=True)
    """
    Categories:
    - evaluation_complete
    - sla_reminder
    - sla_breach
    - subscription_expiring
    - subscription_expired
    - exam_limit_warning
    - performance_report
    - teacher_assignment
    - parent_update
    - system_announcement
    """

    priority = Column(PgEnum('mv_notification_priority', 20), default='medium', nullable=False)
    """Priority: low, medium, high, urgent"""

    # Content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Delivery channels (array of strings: email, sms, in_app, push)
    notification_types = Column(ARRAY(String), nullable=False)

    # Status
    status = Column(String(20), default='pending', nullable=False, index=True)
    """Status: pending, sent, failed, read"""

    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True))

    # Optional action
    action_url = Column(String(500))

    # Additional metadata (JSON) - using extra_data instead of 'metadata' which is reserved
    extra_data = Column(JSONB)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    sent_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))  # Auto-delete after this date

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification {self.notification_id} - {self.category} to {self.user_id}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "notification_id": str(self.notification_id),
            "user_id": str(self.user_id),
            "category": self.category,
            "priority": self.priority,
            "title": self.title,
            "message": self.message,
            "notification_types": self.notification_types,
            "status": self.status,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "action_url": self.action_url,
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class NotificationPreference(Base):
    """User preferences for notification delivery"""

    __tablename__ = "notification_preferences"

    # Primary Key
    preference_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User (one preference record per user)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False, unique=True, index=True)

    # Channel preferences (global switches)
    email_enabled = Column(Boolean, default=True, nullable=False)
    sms_enabled = Column(Boolean, default=False, nullable=False)
    in_app_enabled = Column(Boolean, default=True, nullable=False)
    push_enabled = Column(Boolean, default=False, nullable=False)

    # Category preferences
    evaluation_complete = Column(Boolean, default=True, nullable=False)
    sla_reminders = Column(Boolean, default=True, nullable=False)
    subscription_alerts = Column(Boolean, default=True, nullable=False)
    performance_reports = Column(Boolean, default=True, nullable=False)
    parent_updates = Column(Boolean, default=True, nullable=False)
    system_announcements = Column(Boolean, default=True, nullable=False)

    # Digest settings
    daily_digest = Column(Boolean, default=False, nullable=False)
    weekly_digest = Column(Boolean, default=False, nullable=False)

    # Audit
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="notification_preferences")

    def __repr__(self):
        return f"<NotificationPreference for user {self.user_id}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "preference_id": str(self.preference_id),
            "user_id": str(self.user_id),
            "email_enabled": self.email_enabled,
            "sms_enabled": self.sms_enabled,
            "in_app_enabled": self.in_app_enabled,
            "push_enabled": self.push_enabled,
            "evaluation_complete": self.evaluation_complete,
            "sla_reminders": self.sla_reminders,
            "subscription_alerts": self.subscription_alerts,
            "performance_reports": self.performance_reports,
            "parent_updates": self.parent_updates,
            "system_announcements": self.system_announcements,
            "daily_digest": self.daily_digest,
            "weekly_digest": self.weekly_digest,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
