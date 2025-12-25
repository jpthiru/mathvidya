"""
User Model

SQLAlchemy model for users table.
Supports four roles: student, parent, teacher, admin.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import TypeDecorator
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


class User(Base):
    """User model for all user types"""

    __tablename__ = "users"

    # Primary Key
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    # Use PgEnum to properly cast to PostgreSQL enum type
    role = Column(PgEnum('mv_user_role', 20), nullable=False, index=True)

    # Profile Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))

    # Student-specific fields
    student_class = Column(String(10))  # 'X' or 'XII'
    student_photo_url = Column(Text)
    school_name = Column(String(255))

    # Status flags
    is_active = Column(Boolean, default=True, index=True)
    email_verified = Column(Boolean, default=False)

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login_at = Column(DateTime(timezone=True))

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "(role != 'student') OR (student_class IS NOT NULL)",
            name='mv_student_class_required'
        ),
    )

    # Relationships (uncomment when other models are created)
    # As parent
    # parent_mappings = relationship("ParentStudentMapping", foreign_keys="[ParentStudentMapping.parent_user_id]", back_populates="parent")
    # As student
    # student_mappings = relationship("ParentStudentMapping", foreign_keys="[ParentStudentMapping.student_user_id]", back_populates="student")
    # subscriptions = relationship("Subscription", back_populates="student")
    # exam_instances = relationship("ExamInstance", back_populates="student")
    # evaluations = relationship("Evaluation", back_populates="teacher")
    # created_questions = relationship("Question", back_populates="created_by_user")
    # created_templates = relationship("ExamTemplate", back_populates="created_by_user")
    # Notifications
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship("NotificationPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        """Convert model to dictionary (for API responses)"""
        return {
            "user_id": str(self.user_id),
            "email": self.email,
            "role": self.role,  # role is already a string value via PgEnum
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "phone": self.phone,
            "student_class": self.student_class,
            "is_active": self.is_active,
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
