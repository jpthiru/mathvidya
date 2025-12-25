"""
Question Routes

API endpoints for question bank management.
Accessible by teachers and admins only.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import math

from database import get_session
from models import User
from dependencies.auth import require_teacher_or_admin
from schemas.question import (
    CreateQuestionRequest,
    UpdateQuestionRequest,
    QuestionDetailResponse,
    QuestionSummaryResponse,
    QuestionListResponse,
    BulkQuestionUploadRequest,
    BulkUploadResponse,
    QuestionFilterRequest,
    QuestionStatsResponse,
    UploadQuestionImageRequest,
    UploadQuestionImageResponse,
    ArchiveQuestionRequest,
    CloneQuestionRequest
)
from services import question_service, s3_service


router = APIRouter()


@router.post("/questions", response_model=QuestionDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    request: CreateQuestionRequest,
    current_user: User = Depends(require_teacher_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new question

    - **question_type**: MCQ, VSA, SA, or LA
    - **class_level**: X or XII
    - **unit**: CBSE unit name
    - **question_text**: Question with LaTeX support
    - **marks**: Auto-validated based on question type

    **Permissions**: Teachers and Admins only
    """
    question_data = request.dict()

    question = await question_service.create_question(
        session,
        question_data,
        str(current_user.user_id)
    )

    return QuestionDetailResponse(
        question_id=str(question.question_id),
        question_type=question.question_type,
        class_level=question.class_level,
        unit=question.unit,
        chapter=question.chapter,
        topic=question.topic,
        question_text=question.question_text,
        question_image_url=question.question_image_url,
        options=question.options,
        correct_option=question.correct_option,
        model_answer=question.model_answer,
        marking_scheme=question.marking_scheme,
        marks=question.marks,
        difficulty=question.difficulty,
        tags=question.tags,
        status=question.status,
        created_by_user_id=str(question.created_by_user_id) if question.created_by_user_id else None,
        version=question.version,
        created_at=question.created_at,
        updated_at=question.updated_at
    )


@router.get("/questions/{question_id}", response_model=QuestionDetailResponse)
async def get_question(
    question_id: str,
    current_user: User = Depends(require_teacher_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Get question details by ID

    **Permissions**: Teachers and Admins only
    """
    question = await question_service.get_question_by_id(session, question_id)

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    return QuestionDetailResponse(
        question_id=str(question.question_id),
        question_type=question.question_type,
        class_level=question.class_level,
        unit=question.unit,
        chapter=question.chapter,
        topic=question.topic,
        question_text=question.question_text,
        question_image_url=question.question_image_url,
        options=question.options,
        correct_option=question.correct_option,
        model_answer=question.model_answer,
        marking_scheme=question.marking_scheme,
        marks=question.marks,
        difficulty=question.difficulty,
        tags=question.tags,
        status=question.status,
        created_by_user_id=str(question.created_by_user_id) if question.created_by_user_id else None,
        version=question.version,
        created_at=question.created_at,
        updated_at=question.updated_at
    )


@router.put("/questions/{question_id}", response_model=QuestionDetailResponse)
async def update_question(
    question_id: str,
    request: UpdateQuestionRequest,
    current_user: User = Depends(require_teacher_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Update a question

    - Only provided fields will be updated
    - Version number auto-increments
    - Cannot change question_type or marks

    **Permissions**: Teachers and Admins only
    """
    update_data = request.dict(exclude_unset=True)

    question = await question_service.update_question(
        session,
        question_id,
        update_data,
        str(current_user.user_id)
    )

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    return QuestionDetailResponse(
        question_id=str(question.question_id),
        question_type=question.question_type,
        class_level=question.class_level,
        unit=question.unit,
        chapter=question.chapter,
        topic=question.topic,
        question_text=question.question_text,
        question_image_url=question.question_image_url,
        options=question.options,
        correct_option=question.correct_option,
        model_answer=question.model_answer,
        marking_scheme=question.marking_scheme,
        marks=question.marks,
        difficulty=question.difficulty,
        tags=question.tags,
        status=question.status,
        created_by_user_id=str(question.created_by_user_id) if question.created_by_user_id else None,
        version=question.version,
        created_at=question.created_at,
        updated_at=question.updated_at
    )


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: str,
    request: Optional[ArchiveQuestionRequest] = None,
    current_user: User = Depends(require_teacher_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Archive (soft delete) a question

    - Question status set to 'archived'
    - Not permanently deleted
    - Cannot be used in future exams

    **Permissions**: Teachers and Admins only
    """
    success = await question_service.delete_question(session, question_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    return None


@router.post("/questions/{question_id}/activate", response_model=QuestionDetailResponse)
async def activate_question(
    question_id: str,
    current_user: User = Depends(require_teacher_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Activate a question (make available for exams)

    - Changes status from 'draft' or 'archived' to 'active'
    - Only active questions appear in exam generation

    **Permissions**: Teachers and Admins only
    """
    question = await question_service.activate_question(session, question_id)

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    return QuestionDetailResponse(
        question_id=str(question.question_id),
        question_type=question.question_type,
        class_level=question.class_level,
        unit=question.unit,
        chapter=question.chapter,
        topic=question.topic,
        question_text=question.question_text,
        question_image_url=question.question_image_url,
        options=question.options,
        correct_option=question.correct_option,
        model_answer=question.model_answer,
        marking_scheme=question.marking_scheme,
        marks=question.marks,
        difficulty=question.difficulty,
        tags=question.tags,
        status=question.status,
        created_by_user_id=str(question.created_by_user_id) if question.created_by_user_id else None,
        version=question.version,
        created_at=question.created_at,
        updated_at=question.updated_at
    )


@router.post("/questions/search", response_model=QuestionListResponse)
async def search_questions(
    filters: QuestionFilterRequest,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    current_user: User = Depends(require_teacher_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Search questions with filters

    - Supports filtering by type, class, unit, difficulty, status
    - Full-text search in question_text
    - Tag-based filtering
    - Paginated results

    **Permissions**: Teachers and Admins only
    """
    filter_dict = filters.dict(exclude_unset=True)

    questions, total = await question_service.search_questions(
        session,
        filter_dict,
        page,
        page_size
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    question_summaries = [
        QuestionSummaryResponse(
            question_id=str(q.question_id),
            question_type=q.question_type,
            class_level=q.class_level,
            unit=q.unit,
            question_text=q.question_text[:200] + "..." if len(q.question_text) > 200 else q.question_text,
            marks=q.marks,
            difficulty=q.difficulty,
            status=q.status,
            created_at=q.created_at
        )
        for q in questions
    ]

    return QuestionListResponse(
        questions=question_summaries,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/questions/stats/overview", response_model=QuestionStatsResponse)
async def get_question_stats(
    current_user: User = Depends(require_teacher_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Get question bank statistics

    - Total questions count
    - Breakdown by type, class, unit, status, difficulty
    - Useful for admin dashboard

    **Permissions**: Teachers and Admins only
    """
    stats = await question_service.get_question_stats(session)

    return QuestionStatsResponse(
        total_questions=stats['total_questions'],
        by_type=stats['by_type'],
        by_class=stats['by_class'],
        by_unit=stats['by_unit'],
        by_status=stats['by_status'],
        by_difficulty=stats['by_difficulty']
    )


@router.post("/questions/bulk", response_model=BulkUploadResponse)
async def bulk_create_questions(
    request: BulkQuestionUploadRequest,
    current_user: User = Depends(require_teacher_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Upload multiple questions at once

    - Maximum 50 questions per request
    - Partial success: some may succeed even if others fail
    - Returns list of errors for failed questions

    **Permissions**: Teachers and Admins only
    """
    questions_data = [q.dict() for q in request.questions]

    created, errors = await question_service.bulk_create_questions(
        session,
        questions_data,
        str(current_user.user_id)
    )

    return BulkUploadResponse(
        total_submitted=len(questions_data),
        successful=len(created),
        failed=len(errors),
        errors=errors,
        created_question_ids=[str(q.question_id) for q in created]
    )


@router.post("/questions/{question_id}/clone", response_model=QuestionDetailResponse)
async def clone_question(
    question_id: str,
    request: Optional[CloneQuestionRequest] = None,
    current_user: User = Depends(require_teacher_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Clone a question with optional modifications

    - Creates duplicate of existing question
    - Optionally modify fields in the clone
    - New question starts as 'draft'

    **Permissions**: Teachers and Admins only
    """
    modifications = None
    if request and request.modifications:
        modifications = request.modifications.dict(exclude_unset=True)

    cloned = await question_service.clone_question(
        session,
        question_id,
        str(current_user.user_id),
        modifications
    )

    if not cloned:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original question not found"
        )

    return QuestionDetailResponse(
        question_id=str(cloned.question_id),
        question_type=cloned.question_type,
        class_level=cloned.class_level,
        unit=cloned.unit,
        chapter=cloned.chapter,
        topic=cloned.topic,
        question_text=cloned.question_text,
        question_image_url=cloned.question_image_url,
        options=cloned.options,
        correct_option=cloned.correct_option,
        model_answer=cloned.model_answer,
        marking_scheme=cloned.marking_scheme,
        marks=cloned.marks,
        difficulty=cloned.difficulty,
        tags=cloned.tags,
        status=cloned.status,
        created_by_user_id=str(cloned.created_by_user_id) if cloned.created_by_user_id else None,
        version=cloned.version,
        created_at=cloned.created_at,
        updated_at=cloned.updated_at
    )


@router.post("/questions/{question_id}/upload-image", response_model=UploadQuestionImageResponse)
async def get_question_image_upload_url(
    question_id: str,
    request: UploadQuestionImageRequest,
    current_user: User = Depends(require_teacher_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Get presigned URL for uploading question image

    - Question images stored in S3
    - Supports diagrams, graphs, equations
    - Returns URL valid for 15 minutes

    **Permissions**: Teachers and Admins only
    """
    # Verify question exists
    question = await question_service.get_question_by_id(session, question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    # Generate S3 key
    file_extension = request.file_name.split('.')[-1] if '.' in request.file_name else 'jpg'
    s3_key = s3_service.generate_question_image_key(question_id, file_extension)

    # Generate presigned URL
    presigned_url = s3_service.generate_presigned_upload_url(s3_key)

    if not presigned_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate upload URL"
        )

    # Update question with image URL (base URL, actual URL will be full S3 path)
    # In production, update after confirming upload
    from config.settings import settings
    question.question_image_url = f"https://{settings.S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
    await session.commit()

    return UploadQuestionImageResponse(
        question_id=question_id,
        presigned_url=presigned_url,
        s3_key=s3_key,
        expires_in=900  # 15 minutes
    )
