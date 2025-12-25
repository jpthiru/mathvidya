"""
System Models

System-wide tables:
- AuditLog: Immutable audit trail for all critical actions
- Holiday: Holiday calendar for SLA working-day calculations
- SystemConfig: System-wide configuration key-value store
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint, Date, Text, Boolean, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from database import Base
from models.enums import UserRole

class PgEnum(TypeDecorator):
    """Custom type to handle PostgreSQL ENUMs as strings

    This decorator wraps String columns to properly cast values to PostgreSQL enum types.
    It generates SQL like: CAST(:param AS enum_type_name)
    """
    impl = String
    cache_ok = True

    def __init__(self, enum_type_name, *args, **kwargs):
        self.enum_type_name = enum_type_name
        super().__init__(*args, **kwargs)

    def bind_expression(self, bindvalue):
        #  Use text() to create a custom type reference for casting
        from sqlalchemy import text
        # Create a type clause that can be used in CAST
        from sqlalchemy.dialects.postgresql import ENUM
        # Create an anonymous enum type just for the cast
        enum_type = ENUM(name=self.enum_type_name, create_type=False)
        from sqlalchemy import cast
        return cast(bindvalue, enum_type)

class AuditLog(Base):
    """Immutable audit trail for all critical system actions"""

    __tablename__ = "audit_logs"

    # Primary Key
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Event classification
    event_type = Column(String(100), nullable=False, index=True)
    """
    Event types:
    - 'user.login', 'user.logout', 'user.role_changed'
    - 'exam.started', 'exam.submitted', 'exam.evaluated'
    - 'evaluation.assigned', 'evaluation.started', 'evaluation.completed'
    - 'score.updated', 'subscription.created', 'subscription.expired'
    - 'config.updated', 'question.created', 'question.updated'
    """

    # Actor (who did it)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), index=True)
    actor_role = Column(PgEnum('mv_user_role', 20))
    actor_ip = Column(INET)  # IP address

    # Target (what was affected)
    resource_type = Column(String(50))  # 'exam', 'evaluation', 'user', 'subscription', 'config'
    resource_id = Column(UUID(as_uuid=True))

    # Event details (flexible JSON)
    event_data = Column(JSONB)
    """
    Example for 'evaluation.completed':
    {
      "exam_instance_id": "uuid",
      "teacher_id": "uuid",
      "student_id": "uuid",
      "total_marks": 75.5,
      "sla_breached": false,
      "completion_time_hours": 22.5
    }
    """

    # Timestamp (immutable)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Note: Immutability triggers will be added in migration (prevent UPDATE/DELETE)

    # Relationships
    # actor = relationship("User")

    def __repr__(self):
        return f"<AuditLog {self.event_type} by {self.actor_user_id} at {self.created_at}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "log_id": str(self.log_id),
            "event_type": self.event_type,
            "actor_user_id": str(self.actor_user_id) if self.actor_user_id else None,
            "actor_role": self.actor_role if self.actor_role else None,
            "actor_ip": str(self.actor_ip) if self.actor_ip else None,
            "resource_type": self.resource_type,
            "resource_id": str(self.resource_id) if self.resource_id else None,
            "event_data": self.event_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Holiday(Base):
    """Holiday calendar for SLA working-day calculations"""

    __tablename__ = "holidays"

    # Primary Key
    holiday_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Holiday details
    holiday_date = Column(Date, unique=True, nullable=False, index=True)
    holiday_name = Column(String(255), nullable=False)
    holiday_type = Column(String(50))  # 'national', 'regional', 'system_maintenance'

    # Override: working day despite being Sunday
    is_working_day = Column(Boolean, default=False, nullable=False)

    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'holiday_date >= \'2024-01-01\'',
            name='mv_recent_or_future_holiday'
        ),
    )

    def __repr__(self):
        return f"<Holiday {self.holiday_date} - {self.holiday_name}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "holiday_id": str(self.holiday_id),
            "holiday_date": self.holiday_date.isoformat() if self.holiday_date else None,
            "holiday_name": self.holiday_name,
            "holiday_type": self.holiday_type,
            "is_working_day": self.is_working_day,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SystemConfig(Base):
    """System-wide configuration as JSON key-value pairs"""

    __tablename__ = "system_config"

    # Primary Key
    config_key = Column(String(100), primary_key=True)

    # Configuration
    config_value = Column(JSONB, nullable=False)
    description = Column(Text)

    # Audit
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'config_value IS NOT NULL',
            name='mv_config_value_required'
        ),
    )

    # Relationships
    # updater = relationship("User")

    def __repr__(self):
        return f"<SystemConfig {self.config_key}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "config_key": self.config_key,
            "config_value": self.config_value,
            "description": self.description,
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_value(self):
        """Get the config value"""
        return self.config_value
