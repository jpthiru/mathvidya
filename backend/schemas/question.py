"""
Question Schemas

Pydantic models for question bank management.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from models.enums import QuestionType, QuestionDifficulty, QuestionStatus


class CreateQuestionRequest(BaseModel):
    """Create a new question"""
    question_type: QuestionType
    class_level: str = Field(..., pattern="^(X|XII)$", description="Class X or XII")
    unit: str = Field(..., min_length=1, max_length=100, description="CBSE Unit name")
    chapter: Optional[str] = Field(None, max_length=100)
    topic: Optional[str] = Field(None, max_length=100)

    question_text: str = Field(..., min_length=10, description="Question text with LaTeX support")
    question_image_url: Optional[str] = None

    # MCQ specific
    options: Optional[List[str]] = Field(None, min_items=4, max_items=4, description="Exactly 4 options for MCQ")
    correct_option: Optional[str] = Field(None, pattern="^[A-D]$", description="A, B, C, or D")

    # Descriptive questions
    model_answer: Optional[str] = Field(None, description="Model answer for teacher reference")
    marking_scheme: Optional[str] = Field(None, description="Marking scheme breakdown")

    # Metadata
    marks: int = Field(..., ge=1, le=10, description="Marks for this question")
    difficulty: Optional[QuestionDifficulty] = QuestionDifficulty.MEDIUM
    tags: Optional[List[str]] = Field(None, description="Additional tags for categorization")

    @validator('options')
    def validate_options_for_mcq(cls, v, values):
        """Ensure options are provided for MCQ"""
        if values.get('question_type') == QuestionType.MCQ and not v:
            raise ValueError("Options are required for MCQ questions")
        if values.get('question_type') == QuestionType.MCQ and len(v) != 4:
            raise ValueError("MCQ must have exactly 4 options")
        return v

    @validator('correct_option')
    def validate_correct_option_for_mcq(cls, v, values):
        """Ensure correct_option is provided for MCQ"""
        if values.get('question_type') == QuestionType.MCQ and not v:
            raise ValueError("correct_option is required for MCQ questions")
        return v

    @validator('marks')
    def validate_marks_for_question_type(cls, v, values):
        """Validate marks based on question type"""
        question_type = values.get('question_type')
        if question_type == QuestionType.MCQ and v != 1:
            raise ValueError("MCQ questions must be 1 mark")
        elif question_type == QuestionType.VSA and v != 2:
            raise ValueError("VSA questions must be 2 marks")
        elif question_type == QuestionType.SA and v != 3:
            raise ValueError("SA questions must be 3 marks")
        elif question_type == QuestionType.LA and v not in [5, 6]:
            raise ValueError("LA questions must be 5 or 6 marks")
        return v

    class Config:
        use_enum_values = True


class UpdateQuestionRequest(BaseModel):
    """Update an existing question"""
    # Core fields that can be updated
    question_type: Optional[QuestionType] = None
    class_level: Optional[str] = Field(None, pattern="^(X|XII)$", description="Class X or XII")
    unit: Optional[str] = Field(None, min_length=1, max_length=100, description="CBSE Unit name")
    chapter: Optional[str] = Field(None, max_length=100)
    topic: Optional[str] = Field(None, max_length=100)

    question_text: Optional[str] = Field(None, min_length=10)
    question_image_url: Optional[str] = None

    # MCQ specific
    options: Optional[List[str]] = Field(None, min_items=4, max_items=4)
    correct_option: Optional[str] = Field(None, pattern="^[A-D]$")

    # Descriptive questions
    model_answer: Optional[str] = None
    marking_scheme: Optional[str] = None

    # Metadata
    marks: Optional[int] = Field(None, ge=1, le=10, description="Marks for this question")
    difficulty: Optional[QuestionDifficulty] = None
    tags: Optional[List[str]] = None
    status: Optional[QuestionStatus] = None

    class Config:
        use_enum_values = True


class QuestionDetailResponse(BaseModel):
    """Detailed question information"""
    question_id: str
    question_type: str
    class_level: str
    unit: str
    chapter: Optional[str]
    topic: Optional[str]

    question_text: str
    question_image_url: Optional[str]

    # MCQ specific
    options: Optional[List[str]]
    correct_option: Optional[str]

    # Descriptive questions
    model_answer: Optional[str]
    marking_scheme: Optional[str]

    # Metadata
    marks: int
    difficulty: Optional[str]
    tags: Optional[List[str]]
    status: str

    # Verification
    is_verified: bool = True
    verified_by_user_id: Optional[str] = None
    verified_at: Optional[datetime] = None

    # Audit
    created_by_user_id: Optional[str]
    version: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class QuestionSummaryResponse(BaseModel):
    """Summary view of a question (for lists)"""
    question_id: str
    question_type: str
    class_level: str
    unit: str
    question_text: str  # Truncated in service layer
    marks: int
    difficulty: Optional[str]
    status: str
    is_verified: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionListResponse(BaseModel):
    """Paginated list of questions"""
    questions: List[QuestionSummaryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BulkQuestionUploadRequest(BaseModel):
    """Upload multiple questions at once"""
    questions: List[CreateQuestionRequest] = Field(..., min_items=1, max_items=50)


class BulkUploadResponse(BaseModel):
    """Result of bulk upload"""
    total_submitted: int
    successful: int
    failed: int
    errors: List[dict] = []
    created_question_ids: List[str]


class QuestionFilterRequest(BaseModel):
    """Filter criteria for searching questions"""
    question_type: Optional[QuestionType] = None
    class_level: Optional[str] = None
    unit: Optional[str] = None
    chapter: Optional[str] = None
    difficulty: Optional[QuestionDifficulty] = None
    status: Optional[QuestionStatus] = None
    tags: Optional[List[str]] = None
    search_text: Optional[str] = None  # Search in question_text
    is_verified: Optional[bool] = None  # Filter by verification status

    class Config:
        use_enum_values = True


class QuestionStatsResponse(BaseModel):
    """Statistics about question bank"""
    total_questions: int
    by_type: dict  # {"MCQ": 100, "VSA": 50, ...}
    by_class: dict  # {"X": 80, "XII": 120}
    by_unit: dict  # {"Relations and Functions": 20, ...}
    by_status: dict  # {"active": 150, "draft": 30, ...}
    by_difficulty: dict  # {"easy": 50, "medium": 80, "hard": 20}
    by_unit_type: Optional[dict] = None  # {"Relations and Functions": {"MCQ": 10, "VSA": 5}, ...}


class UploadQuestionImageRequest(BaseModel):
    """Request to upload question image"""
    file_name: str
    content_type: Optional[str] = "image/jpeg"  # MIME type of the file


class UploadQuestionImageResponse(BaseModel):
    """Response with presigned URL for image upload"""
    question_id: str
    presigned_url: str
    s3_key: str
    expires_in: int


class ArchiveQuestionRequest(BaseModel):
    """Archive (soft delete) a question"""
    reason: Optional[str] = Field(None, max_length=500)


class CloneQuestionRequest(BaseModel):
    """Clone a question with modifications"""
    modifications: Optional[UpdateQuestionRequest] = None


class CheckDuplicateRequest(BaseModel):
    """Request to check for duplicate questions"""
    question_text: str = Field(..., min_length=10, description="Question text to check")
    class_level: Optional[str] = Field(None, pattern="^(X|XII)$", description="Optional class filter")
    exclude_question_id: Optional[str] = Field(None, description="Question ID to exclude (for updates)")


class CheckDuplicateResponse(BaseModel):
    """Response for duplicate check"""
    is_duplicate: bool
    matching_question: Optional[QuestionSummaryResponse] = None
    message: str


class VerifyQuestionRequest(BaseModel):
    """Request to verify a batch-processed question"""
    pass  # No additional data needed, just the question_id from URL


class VerifyQuestionResponse(BaseModel):
    """Response after verifying a question"""
    question_id: str
    is_verified: bool
    verified_by_user_id: str
    verified_at: datetime
    message: str


class UnverifiedQuestionsStatsResponse(BaseModel):
    """Statistics about unverified questions"""
    total_unverified: int
    by_class: dict  # {"X": 10, "XII": 20}
    by_type: dict  # {"MCQ": 15, "VSA": 10, ...}
    by_unit: dict  # {"Algebra": 5, ...}
