"""
Evaluation Models

Teacher evaluation with SLA tracking:
- Evaluation: Teacher evaluation assignments with SLA deadlines
- QuestionMark: Granular marks per question for analytics
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, Text, Numeric, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from database import Base
from models.enums import EvaluationStatus, QuestionType

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

class Evaluation(Base):
    """Teacher evaluation assignments with SLA tracking (one per exam)"""

    __tablename__ = "evaluations"

    # Primary Key
    evaluation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    exam_instance_id = Column(UUID(as_uuid=True), ForeignKey('exam_instances.exam_instance_id'), nullable=False, unique=True)
    teacher_user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False, index=True)

    # SLA tracking
    assigned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    sla_deadline = Column(DateTime(timezone=True), nullable=False, index=True)
    sla_hours_allocated = Column(Integer, nullable=False)  # 24 or 48
    sla_breached = Column(Boolean, default=False, nullable=False)

    # Status
    status = Column(PgEnum('mv_evaluation_status', 20), default=EvaluationStatus.ASSIGNED, nullable=False, index=True)

    # Completion
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    total_manual_marks = Column(Numeric(6, 2))

    # Annotations (S3 references)
    annotation_data = Column(JSONB)
    """
    Structure:
    {
      "pages": [
        {
          "page_number": 1,
          "annotated_image_s3_key": "teacher-annotations/{eval_id}/page1.jpg",
          "annotations": [
            {"type": "stamp", "x": 100, "y": 200, "stamp": "tick"},
            {"type": "stamp", "x": 150, "y": 300, "stamp": "cross"}
          ]
        }
      ]
    }
    """

    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'sla_hours_allocated IN (24, 48)',
            name='mv_valid_sla_hours'
        ),
        CheckConstraint(
            'total_manual_marks IS NULL OR total_manual_marks >= 0',
            name='mv_valid_total_manual_marks'
        ),
        # Note: We can't enforce the completion constraint in PostgreSQL directly
        # as it would require checking enum values. This will be enforced at application level.
    )

    # Relationships
    # exam_instance = relationship("ExamInstance", back_populates="evaluation")
    # teacher = relationship("User", back_populates="evaluations")
    # question_marks = relationship("QuestionMark", back_populates="evaluation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Evaluation {self.evaluation_id} - Teacher {self.teacher_user_id} ({self.status})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "evaluation_id": str(self.evaluation_id),
            "exam_instance_id": str(self.exam_instance_id),
            "teacher_user_id": str(self.teacher_user_id),
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "sla_deadline": self.sla_deadline.isoformat() if self.sla_deadline else None,
            "sla_hours_allocated": self.sla_hours_allocated,
            "sla_breached": self.sla_breached,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_manual_marks": float(self.total_manual_marks) if self.total_manual_marks else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def is_overdue(self) -> bool:
        """Check if evaluation is overdue (past SLA deadline and not completed)"""
        if self.status == EvaluationStatus.COMPLETED:
            return False
        return datetime.now(timezone.utc) > self.sla_deadline


class QuestionMark(Base):
    """Granular marks per question for analytics and display"""

    __tablename__ = "question_marks"

    # Primary Key
    mark_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    evaluation_id = Column(UUID(as_uuid=True), ForeignKey('evaluations.evaluation_id', ondelete='CASCADE'), nullable=False, index=True)
    exam_instance_id = Column(UUID(as_uuid=True), ForeignKey('exam_instances.exam_instance_id'), nullable=False, index=True)

    # Question reference
    question_number = Column(Integer, nullable=False)
    question_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # For analytics

    # Question details (denormalized for analytics)
    question_type = Column(PgEnum('mv_question_type', 10), nullable=False)
    unit = Column(String(100), index=True)  # For unit-wise analytics

    # Marks
    marks_awarded = Column(Numeric(5, 2), nullable=False)
    marks_possible = Column(Numeric(5, 2), nullable=False)

    # Teacher feedback
    teacher_comment = Column(Text)

    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Constraints
    __table_args__ = (
        UniqueConstraint('evaluation_id', 'question_number', name='mv_unique_evaluation_question'),
        CheckConstraint('marks_awarded >= 0', name='mv_valid_question_marks_awarded'),
        CheckConstraint('marks_possible > 0', name='mv_valid_question_marks_possible'),
        CheckConstraint('marks_awarded <= marks_possible', name='mv_marks_within_limit'),
        CheckConstraint('question_number > 0', name='mv_valid_mark_question_number'),
    )

    # Relationships
    # evaluation = relationship("Evaluation", back_populates="question_marks")
    # exam_instance = relationship("ExamInstance")

    def __repr__(self):
        return f"<QuestionMark Eval {self.evaluation_id} Q{self.question_number} - {self.marks_awarded}/{self.marks_possible}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "mark_id": str(self.mark_id),
            "evaluation_id": str(self.evaluation_id),
            "exam_instance_id": str(self.exam_instance_id),
            "question_number": self.question_number,
            "question_id": str(self.question_id),
            "question_type": self.question_type,
            "unit": self.unit,
            "marks_awarded": float(self.marks_awarded),
            "marks_possible": float(self.marks_possible),
            "teacher_comment": self.teacher_comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def get_percentage(self) -> float:
        """Calculate percentage for this question"""
        if self.marks_possible == 0:
            return 0.0
        return (float(self.marks_awarded) / float(self.marks_possible)) * 100
