"""
Question Model

Question bank with versioning, multi-format support, and CBSE unit tagging.
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, CheckConstraint, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from database import Base
from models.enums import QuestionType, QuestionDifficulty, QuestionStatus

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

class Question(Base):
    """Question bank with versioning and multi-format support"""

    __tablename__ = "questions"

    # Primary Key
    question_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(Integer, default=1, nullable=False)

    # Classification
    class_level = Column('class', String(10), nullable=False)  # 'X' or 'XII'
    unit = Column(String(100), nullable=False)  # CBSE unit name
    chapter = Column(String(100))  # Optional chapter within unit
    topic = Column(String(255))  # Optional topic within unit
    question_type = Column(PgEnum('mv_question_type', 10), nullable=False, index=True)
    marks = Column(Integer, nullable=False)
    difficulty = Column(PgEnum('mv_question_difficulty', 20))

    # Question content (at least one must be non-null)
    question_text = Column(Text)
    question_image_url = Column(Text)  # S3 URL
    diagram_image_url = Column(Text)   # S3 URL for diagrams

    # MCQ-specific - options as JSONB array of strings ["option1", "option2", ...]
    options = Column(JSONB)  # List of option strings for MCQ
    correct_option = Column(String(1))  # 'A', 'B', 'C', or 'D'

    # Answer and explanation
    model_answer = Column(Text)  # Model answer for teacher reference
    marking_scheme = Column(Text)  # Marking scheme breakdown

    # Metadata
    cbse_year = Column(Integer)  # CBSE board exam year (if from past papers)
    tags = Column(ARRAY(String))  # Flexible tagging ['trigonometry', 'hard', 'important']

    # Status
    status = Column(PgEnum('mv_question_status', 20), default=QuestionStatus.DRAFT, nullable=False, index=True)

    # Audit
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'question_text IS NOT NULL OR question_image_url IS NOT NULL',
            name='mv_question_content_required'
        ),
        CheckConstraint(
            'question_type != \'MCQ\' OR (options IS NOT NULL AND correct_option IS NOT NULL)',
            name='mv_mcq_data_required'
        ),
        CheckConstraint(
            '(question_type = \'MCQ\' AND marks = 1) OR '
            '(question_type = \'VSA\' AND marks = 2) OR '
            '(question_type = \'SA\' AND marks = 3) OR '
            '(question_type = \'LA\' AND marks IN (5, 6))',
            name='mv_marks_match_type'
        ),
        CheckConstraint(
            'class IN (\'X\', \'XII\')',
            name='mv_valid_class'
        ),
        CheckConstraint(
            'version > 0',
            name='mv_valid_version'
        ),
        CheckConstraint(
            'cbse_year IS NULL OR (cbse_year >= 2000 AND cbse_year <= 2100)',
            name='mv_valid_cbse_year'
        ),
    )

    # Relationships
    # created_by_user = relationship("User", back_populates="created_questions")

    def __repr__(self):
        return f"<Question {self.question_id} - {self.question_type} ({self.marks}m) - {self.unit}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "question_id": str(self.question_id),
            "version": self.version,
            "class": self.class_level,
            "unit": self.unit,
            "chapter": self.chapter,
            "topic": self.topic,
            "question_type": self.question_type,
            "marks": self.marks,
            "difficulty": self.difficulty if self.difficulty else None,
            "question_text": self.question_text,
            "question_image_url": self.question_image_url,
            "diagram_image_url": self.diagram_image_url,
            "options": self.options,
            "correct_option": self.correct_option,
            "model_answer": self.model_answer,
            "marking_scheme": self.marking_scheme,
            "cbse_year": self.cbse_year,
            "tags": self.tags,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def is_mcq(self) -> bool:
        """Check if question is MCQ type"""
        return self.question_type == QuestionType.MCQ

    def requires_manual_evaluation(self) -> bool:
        """Check if question requires teacher evaluation"""
        return self.question_type in [QuestionType.VSA, QuestionType.SA, QuestionType.LA]
