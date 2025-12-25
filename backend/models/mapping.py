"""
Parent-Student Mapping Model

Links parents to their children for access control and visibility.
Child data protection compliance: students must have parent visibility.
"""

from sqlalchemy import Column, ForeignKey, Boolean, DateTime, CheckConstraint, UniqueConstraint, String, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from database import Base
from models.enums import RelationshipType

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

class ParentStudentMapping(Base):
    """Parent-student relationship mapping"""

    __tablename__ = "parent_student_mappings"

    # Primary Key
    mapping_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    parent_user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    student_user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)

    # Relationship details
    relationship = Column(PgEnum('mv_relationship_type', 20), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)  # Primary contact for billing/notifications

    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Constraints
    __table_args__ = (
        UniqueConstraint('parent_user_id', 'student_user_id', name='mv_unique_parent_student'),
        CheckConstraint('parent_user_id != student_user_id', name='mv_no_self_mapping'),
    )

    # Relationships
    # parent = relationship("User", foreign_keys=[parent_user_id], back_populates="parent_mappings")
    # student = relationship("User", foreign_keys=[student_user_id], back_populates="student_mappings")

    def __repr__(self):
        return f"<ParentStudentMapping parent={self.parent_user_id} student={self.student_user_id} ({self.relationship})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "mapping_id": str(self.mapping_id),
            "parent_user_id": str(self.parent_user_id),
            "student_user_id": str(self.student_user_id),
            "relationship": self.relationship,
            "is_primary": self.is_primary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
