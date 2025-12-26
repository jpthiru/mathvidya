"""
Exam Instance Models

Individual exam attempts with:
- ExamInstance: Main exam with immutable snapshots
- StudentMCQAnswer: MCQ answers with auto-evaluation
- AnswerSheetUpload: S3 references for scanned answer sheets
- UnansweredQuestion: Student-declared unanswered questions
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, CheckConstraint, BigInteger, Text, UniqueConstraint, Numeric, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from database import Base
from models.enums import ExamType, ExamStatus

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

class ExamInstance(Base):
    """Individual exam attempts with immutable question snapshots"""

    __tablename__ = "exam_instances"

    # Primary Key
    exam_instance_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    student_user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey('exam_templates.template_id'), nullable=True)  # Nullable for unit practice exams

    # Immutable snapshot of exam (questions + template config)
    exam_snapshot = Column(JSONB, nullable=False)
    """
    Structure:
    {
      "template_config": {...},
      "questions": [
        {
          "question_number": 1,
          "section": "A",
          "question_id": "uuid",
          "version": 1,
          "marks": 1,
          "question_type": "MCQ",
          "question_content": {...full question data...}
        }
      ]
    }
    """

    # Exam metadata (denormalized for performance)
    exam_type = Column(PgEnum('mv_exam_type', 30), nullable=False)
    class_level = Column('class', String(10), nullable=False)
    total_marks = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=False)

    # Timing
    started_at = Column(DateTime(timezone=True))
    submitted_at = Column(DateTime(timezone=True))
    time_taken_minutes = Column(Integer)

    # Status
    status = Column(PgEnum('mv_exam_status', 30), default=ExamStatus.CREATED, nullable=False, index=True)

    # Scores (updated as evaluation progresses)
    mcq_score = Column(Numeric(6, 2), default=0)
    manual_score = Column(Numeric(6, 2), default=0)
    total_score = Column(Numeric(6, 2), default=0)
    percentage = Column(Numeric(5, 2))

    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Constraints
    __table_args__ = (
        CheckConstraint('submitted_at IS NULL OR submitted_at >= started_at', name='mv_valid_timing'),
        CheckConstraint('total_score <= total_marks', name='mv_total_score_valid'),
        CheckConstraint('percentage IS NULL OR (percentage >= 0 AND percentage <= 100)', name='mv_valid_percentage'),
        CheckConstraint('mcq_score >= 0', name='mv_valid_mcq_score'),
        CheckConstraint('manual_score >= 0', name='mv_valid_manual_score'),
        CheckConstraint('total_score >= 0', name='mv_valid_total_score'),
    )

    # Relationships
    # student = relationship("User", back_populates="exam_instances")
    # template = relationship("ExamTemplate", back_populates="exam_instances")
    # mcq_answers = relationship("StudentMCQAnswer", back_populates="exam_instance", cascade="all, delete-orphan")
    # answer_uploads = relationship("AnswerSheetUpload", back_populates="exam_instance", cascade="all, delete-orphan")
    # unanswered_questions = relationship("UnansweredQuestion", back_populates="exam_instance", cascade="all, delete-orphan")
    # evaluation = relationship("Evaluation", back_populates="exam_instance", uselist=False)

    def __repr__(self):
        return f"<ExamInstance {self.exam_instance_id} - Student {self.student_user_id} ({self.status})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "exam_instance_id": str(self.exam_instance_id),
            "student_user_id": str(self.student_user_id),
            "template_id": str(self.template_id),
            "exam_type": self.exam_type,
            "class": self.class_level,
            "total_marks": self.total_marks,
            "duration_minutes": self.duration_minutes,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "time_taken_minutes": self.time_taken_minutes,
            "status": self.status,
            "mcq_score": float(self.mcq_score) if self.mcq_score else 0,
            "manual_score": float(self.manual_score) if self.manual_score else 0,
            "total_score": float(self.total_score) if self.total_score else 0,
            "percentage": float(self.percentage) if self.percentage else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class StudentMCQAnswer(Base):
    """MCQ answers with auto-evaluation results"""

    __tablename__ = "student_mcq_answers"

    # Primary Key
    answer_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    exam_instance_id = Column(UUID(as_uuid=True), ForeignKey('exam_instances.exam_instance_id', ondelete='CASCADE'), nullable=False, index=True)

    # Question reference
    question_number = Column(Integer, nullable=False)
    question_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # For analytics

    # Student's answer
    selected_choices = Column(JSONB, nullable=False)  # ["A"] or ["A", "C"] for multi-select

    # Auto-evaluation (computed immediately)
    is_correct = Column(Boolean, nullable=False)
    marks_awarded = Column(Numeric(5, 2), nullable=False)
    marks_possible = Column(Numeric(5, 2), nullable=False)

    # Timing
    answered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Constraints
    __table_args__ = (
        UniqueConstraint('exam_instance_id', 'question_number', name='mv_unique_exam_question_answer'),
        CheckConstraint('marks_awarded >= 0', name='mv_valid_marks_awarded'),
        CheckConstraint('marks_possible > 0', name='mv_valid_marks_possible'),
        CheckConstraint('question_number > 0', name='mv_valid_question_number'),
    )

    # Relationships
    # exam_instance = relationship("ExamInstance", back_populates="mcq_answers")

    def __repr__(self):
        return f"<StudentMCQAnswer Exam {self.exam_instance_id} Q{self.question_number} - {'Correct' if self.is_correct else 'Wrong'}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "answer_id": str(self.answer_id),
            "exam_instance_id": str(self.exam_instance_id),
            "question_number": self.question_number,
            "question_id": str(self.question_id),
            "selected_choices": self.selected_choices,
            "is_correct": self.is_correct,
            "marks_awarded": float(self.marks_awarded),
            "marks_possible": float(self.marks_possible),
            "answered_at": self.answered_at.isoformat() if self.answered_at else None,
        }


class AnswerSheetUpload(Base):
    """S3 references to scanned handwritten answer sheets"""

    __tablename__ = "answer_sheet_uploads"

    # Primary Key
    upload_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    exam_instance_id = Column(UUID(as_uuid=True), ForeignKey('exam_instances.exam_instance_id', ondelete='CASCADE'), nullable=False, index=True)
    student_user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)

    # Upload details
    page_number = Column(Integer, nullable=False)
    s3_bucket = Column(String(255), nullable=False)
    s3_key = Column(Text, nullable=False, index=True)
    file_size_bytes = Column(BigInteger)
    mime_type = Column(String(100))

    # Question mapping (which questions on this page)
    questions_on_page = Column(JSONB)  # [21, 22, 23, 24, 25]

    # Upload metadata
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Constraints
    __table_args__ = (
        UniqueConstraint('exam_instance_id', 'page_number', name='mv_unique_exam_page'),
        CheckConstraint('page_number > 0', name='mv_valid_page_number'),
        CheckConstraint('file_size_bytes IS NULL OR file_size_bytes > 0', name='mv_valid_file_size'),
    )

    # Relationships
    # exam_instance = relationship("ExamInstance", back_populates="answer_uploads")
    # student = relationship("User")

    def __repr__(self):
        return f"<AnswerSheetUpload Exam {self.exam_instance_id} Page {self.page_number}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "upload_id": str(self.upload_id),
            "exam_instance_id": str(self.exam_instance_id),
            "student_user_id": str(self.student_user_id),
            "page_number": self.page_number,
            "s3_bucket": self.s3_bucket,
            "s3_key": self.s3_key,
            "file_size_bytes": self.file_size_bytes,
            "mime_type": self.mime_type,
            "questions_on_page": self.questions_on_page,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }

    def get_s3_url(self) -> str:
        """Construct S3 URL (for signed URL generation)"""
        return f"s3://{self.s3_bucket}/{self.s3_key}"


class UnansweredQuestion(Base):
    """Student-declared unanswered questions (0 marks, no penalty)"""

    __tablename__ = "unanswered_questions"

    # Primary Key
    record_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    exam_instance_id = Column(UUID(as_uuid=True), ForeignKey('exam_instances.exam_instance_id', ondelete='CASCADE'), nullable=False, index=True)

    # Question reference
    question_number = Column(Integer, nullable=False)

    # Status
    declared_unanswered = Column(Boolean, default=True, nullable=False)

    # Timing
    declared_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Constraints
    __table_args__ = (
        UniqueConstraint('exam_instance_id', 'question_number', name='mv_unique_exam_unanswered'),
        CheckConstraint('question_number > 0', name='mv_valid_unanswered_question_number'),
    )

    # Relationships
    # exam_instance = relationship("ExamInstance", back_populates="unanswered_questions")

    def __repr__(self):
        return f"<UnansweredQuestion Exam {self.exam_instance_id} Q{self.question_number}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "record_id": str(self.record_id),
            "exam_instance_id": str(self.exam_instance_id),
            "question_number": self.question_number,
            "declared_unanswered": self.declared_unanswered,
            "declared_at": self.declared_at.isoformat() if self.declared_at else None,
        }
