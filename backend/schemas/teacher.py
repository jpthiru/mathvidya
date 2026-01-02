"""
Teacher Schemas

Pydantic models for teacher-specific endpoints including student management.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== Student List ====================

class StudentListItem(BaseModel):
    """Single student in the list"""
    student_id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    student_class: str
    school_name: Optional[str] = None

    # Performance summary
    total_exams: int = 0
    exams_evaluated: int = 0
    average_percentage: Optional[float] = None
    last_exam_date: Optional[datetime] = None

    # Status
    is_active: bool = True
    created_at: datetime


class StudentListResponse(BaseModel):
    """Paginated list of students"""
    students: List[StudentListItem] = Field(default_factory=list)
    total: int
    page: int
    page_size: int
    total_pages: int


class StudentSearchFilters(BaseModel):
    """Filters for student search"""
    search: Optional[str] = Field(None, description="Search by email, name")
    student_class: Optional[str] = Field(None, pattern="^(X|XII)$")
    has_exams: Optional[bool] = Field(None, description="Filter students who have taken exams")
    min_average: Optional[float] = Field(None, ge=0, le=100)
    max_average: Optional[float] = Field(None, ge=0, le=100)


# ==================== Student Exams ====================

class StudentExamListItem(BaseModel):
    """Single exam in student's exam list"""
    exam_instance_id: str
    exam_type: str

    started_at: datetime
    submitted_at: Optional[datetime] = None
    evaluated_at: Optional[datetime] = None

    status: str
    total_marks: int
    mcq_score: Optional[float] = None
    total_score: Optional[float] = None
    percentage: Optional[float] = None

    # Question breakdown
    total_questions: int
    mcq_count: int = 0
    vsa_count: int = 0
    sa_count: int = 0

    # Evaluation info
    evaluation_id: Optional[str] = None
    evaluated_by: Optional[str] = None


class StudentExamsResponse(BaseModel):
    """List of student exams"""
    student_id: str
    student_name: str
    student_class: str
    exams: List[StudentExamListItem] = Field(default_factory=list)
    total: int
    page: int
    page_size: int


# ==================== Teacher Stats ====================

class TeacherStudentStats(BaseModel):
    """Statistics about students for teacher dashboard"""
    total_students: int = 0
    students_with_exams: int = 0
    total_exams_taken: int = 0
    exams_pending_evaluation: int = 0

    # Class breakdown
    class_x_students: int = 0
    class_xii_students: int = 0

    # Performance overview
    avg_student_percentage: Optional[float] = None
    top_performers: int = 0  # Students with avg > 75%
    struggling_students: int = 0  # Students with avg < 40%


# ==================== Exam Feedback (AI-Ready) ====================

class ExamFeedbackBase(BaseModel):
    """Base feedback model"""
    feedback_text: str = Field(..., min_length=1, max_length=2000)
    feedback_type: str = Field(
        default="general",
        description="Type: general, encouragement, correction, explanation"
    )


class QuestionFeedbackCreate(ExamFeedbackBase):
    """Create feedback for a specific question"""
    question_number: int = Field(..., gt=0)


class ExamFeedbackCreate(BaseModel):
    """Create overall exam feedback"""
    overall_feedback: Optional[str] = Field(None, max_length=2000)
    question_feedbacks: List[QuestionFeedbackCreate] = Field(default_factory=list)


class StudentClarificationRequest(BaseModel):
    """Student's clarification request"""
    question_number: int = Field(..., gt=0)
    clarification_text: str = Field(..., min_length=1, max_length=1000)
    attachment_url: Optional[str] = None


class TeacherClarificationResponse(BaseModel):
    """Teacher's response to clarification"""
    response_text: str = Field(..., min_length=1, max_length=2000)
    attachment_url: Optional[str] = None


class FeedbackThreadItem(BaseModel):
    """Single item in feedback thread"""
    id: str
    question_number: int

    # Teacher's initial feedback
    teacher_feedback: Optional[str] = None
    feedback_type: str = "general"
    feedback_created_at: Optional[datetime] = None

    # Student's clarification
    student_question: Optional[str] = None
    student_attachment_url: Optional[str] = None
    student_question_at: Optional[datetime] = None

    # Teacher's response
    teacher_response: Optional[str] = None
    teacher_response_attachment_url: Optional[str] = None
    teacher_response_at: Optional[datetime] = None

    # AI suggestion fields (for future use)
    ai_suggested_feedback: Optional[str] = None
    ai_confidence_score: Optional[float] = None
    teacher_used_ai_suggestion: bool = False


class ExamFeedbackResponse(BaseModel):
    """Complete feedback for an exam"""
    exam_instance_id: str
    evaluation_id: str
    student_id: str
    student_name: str

    overall_feedback: Optional[str] = None
    feedback_threads: List[FeedbackThreadItem] = Field(default_factory=list)

    # Stats
    total_feedbacks: int = 0
    pending_clarifications: int = 0

    created_at: datetime
    updated_at: Optional[datetime] = None
