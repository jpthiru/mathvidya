"""
Exam Feedback Model

AI-ready feedback system for teacher-student communication on exam evaluations.
Supports:
- Teacher feedback per question
- Student clarification requests
- Teacher responses to clarifications
- AI-suggested feedback fields for future integration
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, Float, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from database import Base


class FeedbackType(str, enum.Enum):
    """Types of feedback"""
    GENERAL = "general"
    ENCOURAGEMENT = "encouragement"
    CORRECTION = "correction"
    EXPLANATION = "explanation"


class FeedbackStatus(str, enum.Enum):
    """Status of feedback thread"""
    OPEN = "open"  # Teacher feedback provided, awaiting student action
    CLARIFICATION_REQUESTED = "clarification_requested"  # Student asked for clarification
    RESPONDED = "responded"  # Teacher responded to clarification
    CLOSED = "closed"  # Thread closed, no further action needed


class ExamFeedback(Base):
    """
    Exam-level feedback container.
    One record per evaluated exam.
    """

    __tablename__ = "exam_feedbacks"

    # Primary Key
    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    evaluation_id = Column(
        UUID(as_uuid=True),
        ForeignKey('evaluations.evaluation_id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        index=True
    )
    exam_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey('exam_instances.exam_instance_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    student_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    teacher_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.user_id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    # Overall feedback for the exam
    overall_feedback = Column(Text, nullable=True)

    # Stats
    total_question_feedbacks = Column(Integer, default=0)
    pending_clarifications = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    question_feedbacks = relationship(
        "QuestionFeedback",
        back_populates="exam_feedback",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ExamFeedback {self.feedback_id} for Exam {self.exam_instance_id}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "feedback_id": str(self.feedback_id),
            "evaluation_id": str(self.evaluation_id),
            "exam_instance_id": str(self.exam_instance_id),
            "student_user_id": str(self.student_user_id),
            "teacher_user_id": str(self.teacher_user_id) if self.teacher_user_id else None,
            "overall_feedback": self.overall_feedback,
            "total_question_feedbacks": self.total_question_feedbacks,
            "pending_clarifications": self.pending_clarifications,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class QuestionFeedback(Base):
    """
    Per-question feedback thread.
    Supports teacher feedback, student clarification, and teacher response.
    AI-ready with fields for suggested feedback.
    """

    __tablename__ = "question_feedbacks"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Parent relationship
    exam_feedback_id = Column(
        UUID(as_uuid=True),
        ForeignKey('exam_feedbacks.feedback_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Question reference
    question_number = Column(Integer, nullable=False)
    question_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Thread status
    status = Column(String(30), default=FeedbackStatus.OPEN.value, nullable=False)

    # ========== Teacher's Initial Feedback ==========
    teacher_feedback = Column(Text, nullable=True)
    feedback_type = Column(String(20), default=FeedbackType.GENERAL.value)
    feedback_created_at = Column(DateTime(timezone=True))

    # ========== Student Clarification Request ==========
    student_question = Column(Text, nullable=True)
    student_attachment_url = Column(String(500), nullable=True)  # S3 URL for image/PDF
    student_question_at = Column(DateTime(timezone=True))

    # ========== Teacher Response to Clarification ==========
    teacher_response = Column(Text, nullable=True)
    teacher_response_attachment_url = Column(String(500), nullable=True)
    teacher_response_at = Column(DateTime(timezone=True))

    # ========== AI Suggestion Fields (Future Use) ==========
    ai_suggested_feedback = Column(Text, nullable=True)
    ai_confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    teacher_used_ai_suggestion = Column(Boolean, default=False)
    ai_model_version = Column(String(50), nullable=True)  # Track which AI model version
    ai_generated_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    exam_feedback = relationship("ExamFeedback", back_populates="question_feedbacks")

    def __repr__(self):
        return f"<QuestionFeedback Q{self.question_number} for Exam {self.exam_feedback_id}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "exam_feedback_id": str(self.exam_feedback_id),
            "question_number": self.question_number,
            "question_id": str(self.question_id),
            "status": self.status,
            # Teacher feedback
            "teacher_feedback": self.teacher_feedback,
            "feedback_type": self.feedback_type,
            "feedback_created_at": self.feedback_created_at.isoformat() if self.feedback_created_at else None,
            # Student clarification
            "student_question": self.student_question,
            "student_attachment_url": self.student_attachment_url,
            "student_question_at": self.student_question_at.isoformat() if self.student_question_at else None,
            # Teacher response
            "teacher_response": self.teacher_response,
            "teacher_response_attachment_url": self.teacher_response_attachment_url,
            "teacher_response_at": self.teacher_response_at.isoformat() if self.teacher_response_at else None,
            # AI fields
            "ai_suggested_feedback": self.ai_suggested_feedback,
            "ai_confidence_score": self.ai_confidence_score,
            "teacher_used_ai_suggestion": self.teacher_used_ai_suggestion,
            # Timestamps
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def has_pending_clarification(self) -> bool:
        """Check if there's a pending clarification request"""
        return self.status == FeedbackStatus.CLARIFICATION_REQUESTED.value

    def can_student_request_clarification(self) -> bool:
        """Check if student can request clarification (only one per question)"""
        return self.student_question is None
