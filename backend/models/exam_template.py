"""
Exam Template Model

Configurable CBSE exam patterns with sections, marks, and unit weightage.
Configuration-driven approach allows CBSE pattern changes without code changes.
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, CheckConstraint, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from database import Base
from models.enums import ExamType

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

class ExamTemplate(Base):
    """Configurable exam patterns (CBSE board, section-wise, unit-wise)"""

    __tablename__ = "exam_templates"

    # Primary Key
    template_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic details
    template_name = Column(String(255), nullable=False)
    class_level = Column('class', String(10), nullable=False)  # 'X' or 'XII'
    exam_type = Column(PgEnum('mv_exam_type', 30), nullable=False, index=True)

    # Template configuration (JSONB for flexibility)
    config = Column(JSONB, nullable=False)
    """
    Example config structure:
    {
      "total_marks": 80,
      "duration_minutes": 180,
      "sections": [
        {
          "section_name": "A",
          "question_type": "MCQ",
          "marks_per_question": 1,
          "question_count": 20,
          "unit_weightage": {
            "Relations and Functions": 0.15,
            "Algebra": 0.20,
            "Calculus": 0.25,
            "Probability": 0.15,
            "Vectors and 3D": 0.15,
            "Application of Derivatives": 0.10
          }
        },
        {
          "section_name": "B",
          "question_type": "VSA",
          "marks_per_question": 2,
          "question_count": 10,
          "unit_weightage": {...}
        }
      ]
    }
    """

    # For unit-specific practice
    specific_unit = Column(String(100))  # NULL for board exams, required for unit_practice

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'exam_type != \'unit_practice\' OR specific_unit IS NOT NULL',
            name='mv_unit_practice_requires_unit'
        ),
        CheckConstraint(
            'class IN (\'X\', \'XII\')',
            name='mv_valid_class_level'
        ),
    )

    # Relationships
    # created_by_user = relationship("User", back_populates="created_templates")
    # exam_instances = relationship("ExamInstance", back_populates="template")

    def __repr__(self):
        return f"<ExamTemplate {self.template_name} - {self.exam_type} (Class {self.class_level})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "template_id": str(self.template_id),
            "template_name": self.template_name,
            "class": self.class_level,
            "exam_type": self.exam_type,
            "config": self.config,
            "specific_unit": self.specific_unit,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def get_total_marks(self) -> int:
        """Extract total marks from config"""
        return self.config.get('total_marks', 0)

    def get_duration_minutes(self) -> int:
        """Extract duration from config"""
        return self.config.get('duration_minutes', 180)

    def get_sections(self) -> list:
        """Extract sections from config"""
        return self.config.get('sections', [])
