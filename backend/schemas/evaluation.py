"""
Evaluation Schemas

Pydantic models for teacher evaluation workflow.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from models.enums import EvaluationStatus, QuestionType


class QuestionMarkRequest(BaseModel):
    """Request to assign marks for a single question"""
    question_number: int = Field(..., ge=1, description="Question number in exam")
    marks_awarded: Decimal = Field(..., ge=0, description="Marks awarded to student")
    teacher_comment: Optional[str] = Field(None, max_length=500, description="Optional teacher feedback")

    @validator('marks_awarded')
    def validate_marks_precision(cls, v):
        """Ensure marks have at most 2 decimal places"""
        if v.as_tuple().exponent < -2:
            raise ValueError("Marks can have at most 2 decimal places")
        return v

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class AnnotationStamp(BaseModel):
    """Single annotation stamp on answer sheet"""
    type: str = Field(..., pattern="^stamp$", description="Annotation type (only 'stamp' in V1)")
    x: int = Field(..., ge=0, description="X coordinate")
    y: int = Field(..., ge=0, description="Y coordinate")
    stamp: str = Field(..., pattern="^(tick|cross|half)$", description="Stamp type: tick, cross, or half")


class PageAnnotation(BaseModel):
    """Annotations for a single page"""
    page_number: int = Field(..., ge=1, description="Page number")
    annotated_image_s3_key: Optional[str] = Field(None, description="S3 key for annotated image")
    annotations: List[AnnotationStamp] = Field(default_factory=list, description="List of stamps")


class StartEvaluationRequest(BaseModel):
    """Teacher starts evaluation of an exam"""
    # No fields needed - evaluation_id comes from URL


class SubmitMarksRequest(BaseModel):
    """Submit marks for multiple questions"""
    question_marks: List[QuestionMarkRequest] = Field(..., min_items=1, description="Marks for one or more questions")
    annotations: Optional[List[PageAnnotation]] = Field(None, description="Optional page annotations")


class CompleteEvaluationRequest(BaseModel):
    """Complete the evaluation (finalize)"""
    final_comments: Optional[str] = Field(None, max_length=1000, description="Overall feedback for student")


class EvaluationDetailResponse(BaseModel):
    """Detailed evaluation information"""
    evaluation_id: str
    exam_instance_id: str
    teacher_user_id: str

    # SLA tracking
    assigned_at: datetime
    sla_deadline: datetime
    sla_hours_allocated: int
    sla_breached: bool
    is_overdue: bool

    # Status
    status: str

    # Progress
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_manual_marks: Optional[float]

    # Exam details
    exam_info: Optional[Dict[str, Any]] = Field(None, description="Basic exam information")
    student_info: Optional[Dict[str, Any]] = Field(None, description="Student name and details")

    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class EvaluationSummaryResponse(BaseModel):
    """Summary view of evaluation (for lists)"""
    evaluation_id: str
    exam_instance_id: str
    student_name: str
    exam_type: str
    class_level: str
    total_marks: int

    status: str
    assigned_at: datetime
    sla_deadline: datetime
    sla_breached: bool
    is_overdue: bool

    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class EvaluationListResponse(BaseModel):
    """Paginated list of evaluations"""
    evaluations: List[EvaluationSummaryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class QuestionMarkResponse(BaseModel):
    """Marks for a single question"""
    mark_id: str
    evaluation_id: str
    question_number: int
    question_id: str
    question_type: str
    unit: Optional[str]

    marks_awarded: float
    marks_possible: float
    percentage: float

    teacher_comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationProgressResponse(BaseModel):
    """Current evaluation progress"""
    evaluation_id: str
    status: str

    # Question breakdown
    total_questions: int
    questions_evaluated: int
    questions_remaining: int

    # Marks breakdown
    total_possible_marks: float
    marks_awarded: float
    current_percentage: Optional[float]

    # Question marks
    question_marks: List[QuestionMarkResponse]

    # SLA
    sla_deadline: datetime
    is_overdue: bool


class AssignEvaluationRequest(BaseModel):
    """Admin assigns evaluation to teacher"""
    exam_instance_id: str = Field(..., description="Exam to evaluate")
    teacher_user_id: str = Field(..., description="Teacher to assign")
    sla_hours: int = Field(..., description="SLA hours (24 or 48)")

    @validator('sla_hours')
    def validate_sla_hours(cls, v):
        """Ensure SLA is 24 or 48 hours"""
        if v not in [24, 48]:
            raise ValueError("SLA hours must be 24 or 48")
        return v


class AssignEvaluationResponse(BaseModel):
    """Response after assigning evaluation"""
    evaluation_id: str
    exam_instance_id: str
    teacher_user_id: str
    sla_deadline: datetime
    status: str

    class Config:
        from_attributes = True


class PendingEvaluationFilterRequest(BaseModel):
    """Filter criteria for pending evaluations"""
    status: Optional[EvaluationStatus] = None
    class_level: Optional[str] = None
    sla_breached_only: Optional[bool] = Field(None, description="Show only SLA breached")
    overdue_only: Optional[bool] = Field(None, description="Show only overdue")

    class Config:
        use_enum_values = True


class TeacherWorkloadResponse(BaseModel):
    """Teacher's current workload"""
    teacher_user_id: str
    teacher_name: str

    # Counts
    total_assigned: int
    pending_count: int
    in_progress_count: int
    completed_count: int

    # SLA
    overdue_count: int
    sla_breached_count: int

    # Upcoming deadlines
    upcoming_deadlines: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Next 5 evaluations by deadline"
    )


class EvaluationStatsResponse(BaseModel):
    """System-wide evaluation statistics"""
    total_evaluations: int

    # By status
    assigned_count: int
    in_progress_count: int
    completed_count: int

    # SLA metrics
    total_overdue: int
    total_sla_breached: int
    sla_compliance_rate: float

    # Average times
    avg_completion_time_hours: Optional[float]


class UploadAnnotatedImageRequest(BaseModel):
    """Request presigned URL for annotated image upload"""
    evaluation_id: str
    page_number: int = Field(..., ge=1, description="Page number")
    file_name: str = Field(..., description="Original file name")


class UploadAnnotatedImageResponse(BaseModel):
    """Presigned URL for uploading annotated image"""
    evaluation_id: str
    page_number: int
    presigned_url: str
    s3_key: str
    expires_in: int = 900  # 15 minutes

    class Config:
        from_attributes = True


class BulkAssignEvaluationsRequest(BaseModel):
    """Bulk assign multiple evaluations to teachers"""
    assignments: List[AssignEvaluationRequest] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="List of evaluation assignments"
    )


class BulkAssignEvaluationsResponse(BaseModel):
    """Result of bulk assignment"""
    total_submitted: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]] = []
    created_evaluation_ids: List[str]
