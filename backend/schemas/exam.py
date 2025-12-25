"""
Exam Schemas

Pydantic models for exam-related operations.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from models.enums import ExamType, ExamStatus, QuestionType


class ExamTemplateResponse(BaseModel):
    """Exam template information"""
    template_id: str
    template_name: str
    exam_type: str
    class_level: str
    total_marks: int
    duration_minutes: int
    section_config: Dict
    is_active: bool

    class Config:
        from_attributes = True


class StartExamRequest(BaseModel):
    """Request to start a new exam"""
    template_id: str
    exam_type: Optional[str] = None  # Override if needed


class QuestionResponse(BaseModel):
    """Question in an exam"""
    question_id: str
    question_number: int
    question_type: str
    marks: int
    unit: str
    chapter: Optional[str] = None
    topic: Optional[str] = None
    question_text: str
    question_image_url: Optional[str] = None
    options: Optional[List[str]] = None  # For MCQ only
    difficulty: Optional[str] = None


class ExamInstanceResponse(BaseModel):
    """Active exam instance"""
    exam_instance_id: str
    student_user_id: str
    exam_type: str
    status: str
    total_marks: int
    duration_minutes: int
    start_time: datetime
    end_time: Optional[datetime] = None
    questions: List[QuestionResponse]
    mcq_score: Optional[float] = None
    total_score: Optional[float] = None

    class Config:
        from_attributes = True


class SubmitMCQRequest(BaseModel):
    """Submit MCQ answers"""
    exam_instance_id: str
    answers: List[Dict[str, str]]  # [{"question_id": "...", "selected_option": "A"}, ...]

    @validator('answers')
    def validate_answers(cls, v):
        """Ensure each answer has question_id and selected_option"""
        for answer in v:
            if 'question_id' not in answer or 'selected_option' not in answer:
                raise ValueError("Each answer must have question_id and selected_option")
            if answer['selected_option'] not in ['A', 'B', 'C', 'D']:
                raise ValueError("selected_option must be A, B, C, or D")
        return v


class MCQResultResponse(BaseModel):
    """MCQ submission result"""
    exam_instance_id: str
    total_mcq_questions: int
    correct_answers: int
    mcq_score: float
    mcq_percentage: float
    status: str  # Should be 'submitted_mcq'


class UploadAnswerSheetRequest(BaseModel):
    """Request to upload answer sheet"""
    exam_instance_id: str
    question_id: str
    page_number: int
    file_name: str  # Original filename


class UploadAnswerSheetResponse(BaseModel):
    """Answer sheet upload response"""
    upload_id: str
    presigned_url: str  # S3 presigned URL for upload
    expires_in: int  # Seconds


class ConfirmUploadRequest(BaseModel):
    """Confirm answer sheet was uploaded"""
    upload_id: str
    s3_key: str  # S3 object key after upload


class DeclareUnansweredRequest(BaseModel):
    """Declare a question as unanswered"""
    exam_instance_id: str
    question_ids: List[str]
    reason: Optional[str] = Field(None, max_length=500)


class SubmitExamRequest(BaseModel):
    """Final exam submission"""
    exam_instance_id: str


class ExamHistoryResponse(BaseModel):
    """Exam history item"""
    exam_instance_id: str
    exam_type: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_marks: int
    mcq_score: Optional[float] = None
    total_score: Optional[float] = None
    percentage: Optional[float] = None
    evaluated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExamStatusResponse(BaseModel):
    """Current status of an exam"""
    exam_instance_id: str
    status: str
    start_time: datetime
    time_remaining_minutes: Optional[int] = None
    mcq_submitted: bool
    answer_sheets_uploaded: int
    total_answer_sheets_expected: int
    is_submitted: bool
    can_submit: bool  # All required uploads done


class AvailableTemplatesResponse(BaseModel):
    """List of available exam templates"""
    templates: List[ExamTemplateResponse]
    total: int
