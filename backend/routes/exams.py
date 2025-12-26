"""
Exam Routes

API endpoints for exam management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_session
from models import User, ExamInstance, Question
from dependencies.auth import get_current_active_user, require_student
from schemas.exam import (
    AvailableTemplatesResponse,
    ExamTemplateResponse,
    StartExamRequest,
    StartUnitPracticeRequest,
    ExamInstanceResponse,
    QuestionResponse,
    SaveMCQAnswerRequest,
    SaveMCQAnswerResponse,
    SubmitMCQRequest,
    MCQResultResponse,
    UploadAnswerSheetRequest,
    UploadAnswerSheetResponse,
    ConfirmUploadRequest,
    DeclareUnansweredRequest,
    SubmitExamRequest,
    ExamHistoryResponse,
    ExamStatusResponse
)
from services import exam_service, s3_service


router = APIRouter()


@router.get("/exams/templates", response_model=AvailableTemplatesResponse)
async def get_available_templates(
    current_user: User = Depends(require_student),
    session: AsyncSession = Depends(get_session)
):
    """
    Get available exam templates for the current student

    Returns list of exam templates based on student's class
    """
    templates = await exam_service.get_available_templates(
        session,
        current_user.student_class
    )

    template_responses = [
        ExamTemplateResponse(
            template_id=str(t.template_id),
            template_name=t.template_name,
            exam_type=t.exam_type,
            class_level=t.class_level,
            total_marks=t.get_total_marks(),
            duration_minutes=t.get_duration_minutes(),
            section_config=t.config,
            is_active=t.is_active
        )
        for t in templates
    ]

    return {
        "templates": template_responses,
        "total": len(template_responses)
    }


@router.post("/exams/start", response_model=ExamInstanceResponse, status_code=status.HTTP_201_CREATED)
async def start_exam(
    request: StartExamRequest,
    StartUnitPracticeRequest,
    current_user: User = Depends(require_student),
    session: AsyncSession = Depends(get_session)
):
    """
    Start a new exam instance

    - Checks if student has an active exam
    - Creates new exam instance
    - Generates random questions based on template
    - Returns exam with all questions
    """
    try:
        exam_instance, questions = await exam_service.start_exam(
            session,
            str(current_user.user_id),
            request.template_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Convert questions to response format
    question_responses = []
    for idx, q in enumerate(questions, 1):
        question_responses.append(QuestionResponse(
            question_id=str(q.question_id),
            question_number=idx,
            question_type=q.question_type,
            marks=q.marks,
            unit=q.unit,
            chapter=q.chapter,
            topic=q.topic,
            question_text=q.question_text,
            question_image_url=q.question_image_url,
            options=q.options if q.question_type == 'MCQ' else None,
            difficulty=q.difficulty
        ))

    return ExamInstanceResponse(
        exam_instance_id=str(exam_instance.exam_instance_id),
        student_user_id=str(exam_instance.student_user_id),
        exam_type=exam_instance.exam_type,
        status=exam_instance.status,
        total_marks=exam_instance.total_marks,
        duration_minutes=exam_instance.duration_minutes,
        start_time=exam_instance.started_at,
        end_time=exam_instance.submitted_at,
        questions=question_responses,
        mcq_score=exam_instance.mcq_score,
        total_score=exam_instance.total_score
    )


@router.post("/exams/start-unit-practice", response_model=ExamInstanceResponse, status_code=status.HTTP_201_CREATED)
async def start_unit_practice(
    request: StartUnitPracticeRequest,
    current_user: User = Depends(require_student),
    session: AsyncSession = Depends(get_session)
):
    """
    Start a unit practice exam with specific question type

    - Student selects units and question type (MCQ, VSA, SA, LA)
    - System loads available questions up to max limit
    - Returns exam with all questions
    """
    try:
        exam_instance, questions = await exam_service.start_unit_practice(
            session,
            str(current_user.user_id),
            current_user.student_class,
            request.selected_units,
            request.question_type
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Convert questions to response format
    question_responses = []
    for idx, q in enumerate(questions, 1):
        question_responses.append(QuestionResponse(
            question_id=str(q.question_id),
            question_number=idx,
            question_type=q.question_type,
            marks=q.marks,
            unit=q.unit,
            chapter=q.chapter,
            topic=q.topic,
            question_text=q.question_text,
            question_image_url=q.question_image_url,
            options=q.options if q.question_type == 'MCQ' else None,
            difficulty=q.difficulty
        ))

    return ExamInstanceResponse(
        exam_instance_id=str(exam_instance.exam_instance_id),
        student_user_id=str(exam_instance.student_user_id),
        exam_type=exam_instance.exam_type,
        status=exam_instance.status,
        total_marks=exam_instance.total_marks,
        duration_minutes=exam_instance.duration_minutes,
        start_time=exam_instance.started_at,
        end_time=exam_instance.submitted_at,
        questions=question_responses,
        mcq_score=exam_instance.mcq_score,
        total_score=exam_instance.total_score
    )


@router.post("/exams/{exam_instance_id}/mcq", response_model=SaveMCQAnswerResponse)
async def save_mcq_answer(
    exam_instance_id: str,
    request: SaveMCQAnswerRequest,
    current_user: User = Depends(require_student),
    session: AsyncSession = Depends(get_session)
):
    """
    Save a single MCQ answer during exam

    - Saves answer to exam_snapshot for persistence
    - Does not evaluate, just stores the selection
    - Can be called multiple times to update answers
    """
    try:
        await exam_service.save_mcq_answer(
            session,
            exam_instance_id,
            str(current_user.user_id),
            request.question_number,
            request.selected_option
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return SaveMCQAnswerResponse(
        success=True,
        question_number=request.question_number,
        selected_option=request.selected_option
    )


@router.post("/exams/{exam_instance_id}/submit", response_model=MCQResultResponse)
async def submit_exam(
    exam_instance_id: str,
    current_user: User = Depends(require_student),
    session: AsyncSession = Depends(get_session)
):
    """
    Submit the exam and evaluate MCQ answers

    - Retrieves saved answers from exam_snapshot
    - Auto-evaluates MCQ answers
    - Updates exam status to 'evaluated'
    - Returns score and percentage
    """
    try:
        total, correct, score = await exam_service.submit_exam(
            session,
            exam_instance_id,
            str(current_user.user_id)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    percentage = (correct / total * 100) if total > 0 else 0

    return MCQResultResponse(
        exam_instance_id=exam_instance_id,
        total_mcq_questions=total,
        correct_answers=correct,
        mcq_score=score,
        mcq_percentage=round(percentage, 2),
        status="evaluated"
    )


@router.get("/exams/{exam_instance_id}/results")
async def get_exam_results(
    exam_instance_id: str,
    current_user: User = Depends(require_student),
    session: AsyncSession = Depends(get_session)
):
    """
    Get detailed exam results with questions and answers

    - Returns exam details, score, and question-by-question breakdown
    - Only available for evaluated exams
    """
    from sqlalchemy import select

    # Get exam instance
    exam = await session.get(ExamInstance, exam_instance_id)
    if not exam or str(exam.student_user_id) != str(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )

    # Get exam snapshot with question IDs and answers
    snapshot = exam.exam_snapshot or {}
    question_ids = snapshot.get('question_ids', [])
    student_answers = snapshot.get('student_answers', {})

    # Load questions
    questions = []
    correct_count = 0
    incorrect_count = 0
    unanswered_count = 0

    for idx, q_id in enumerate(question_ids, 1):
        question = await session.get(Question, q_id)
        if question:
            student_answer = student_answers.get(str(idx))
            is_correct = student_answer == question.correct_option if student_answer else False

            if student_answer is None:
                unanswered_count += 1
            elif is_correct:
                correct_count += 1
            else:
                incorrect_count += 1

            questions.append({
                "question_id": str(question.question_id),
                "question_number": idx,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "options": question.options,
                "correct_option": question.correct_option,
                "marks": question.marks,
                "unit": question.unit,
                "student_answer": student_answer,
                "is_correct": is_correct,
                "model_answer": question.model_answer,  # Explanation/solution
                "marking_scheme": question.marking_scheme
            })

    # Calculate time taken
    time_taken_minutes = None
    if exam.started_at and exam.submitted_at:
        delta = exam.submitted_at - exam.started_at
        time_taken_minutes = int(delta.total_seconds() / 60)

    return {
        "exam_instance_id": str(exam.exam_instance_id),
        "exam_type": exam.exam_type,
        "class_level": exam.class_level,
        "status": exam.status,
        "started_at": exam.started_at.isoformat() if exam.started_at else None,
        "submitted_at": exam.submitted_at.isoformat() if exam.submitted_at else None,
        "total_marks": exam.total_marks,
        "mcq_score": exam.mcq_score,
        "total_score": exam.total_score,
        "percentage": exam.total_score / exam.total_marks * 100 if exam.total_marks and exam.total_score else 0,
        "total_questions": len(questions),
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "unanswered_count": unanswered_count,
        "time_taken_minutes": time_taken_minutes,
        "questions": questions,
        "answers": student_answers
    }


@router.post("/exams/submit-mcq", response_model=MCQResultResponse)
async def submit_mcq_answers(
    request: SubmitMCQRequest,
    current_user: User = Depends(require_student),
    session: AsyncSession = Depends(get_session)
):
    """
    Submit MCQ answers

    - Auto-evaluates MCQ answers
    - Updates exam status to 'submitted_mcq'
    - Returns score and percentage
    """
    try:
        total, correct, score = await exam_service.submit_mcq_answers(
            session,
            request.exam_instance_id,
            str(current_user.user_id),
            request.answers
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    percentage = (correct / total * 100) if total > 0 else 0

    return MCQResultResponse(
        exam_instance_id=request.exam_instance_id,
        total_mcq_questions=total,
        correct_answers=correct,
        mcq_score=score,
        mcq_percentage=round(percentage, 2),
        status="submitted_mcq"
    )


@router.post("/exams/upload-answer-sheet", response_model=UploadAnswerSheetResponse)
async def get_upload_url(
    request: UploadAnswerSheetRequest,
    current_user: User = Depends(require_student),
    session: AsyncSession = Depends(get_session)
):
    """
    Get presigned URL for uploading answer sheet

    - Generates S3 presigned URL
    - Returns URL valid for 15 minutes
    - Client uploads directly to S3
    """
    # Verify exam belongs to student
    exam = await exam_service.get_exam_status(
        session,
        request.exam_instance_id,
        str(current_user.user_id)
    )

    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )

    # Generate S3 key
    file_extension = request.file_name.split('.')[-1] if '.' in request.file_name else 'jpg'
    s3_key = s3_service.generate_answer_sheet_key(
        str(exam.exam_instance_id),
        request.question_id,
        request.page_number,
        file_extension
    )

    # Generate presigned URL
    presigned_url = s3_service.generate_presigned_upload_url(s3_key)

    if not presigned_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate upload URL"
        )

    # Create upload record
    from models import AnswerSheetUpload
    from datetime import datetime, timezone

    upload = AnswerSheetUpload(
        exam_instance_id=request.exam_instance_id,
        question_id=request.question_id,
        page_number=request.page_number,
        s3_key=s3_key,
        original_filename=request.file_name,
        uploaded_at=datetime.now(timezone.utc)
    )

    session.add(upload)
    await session.commit()
    await session.refresh(upload)

    return UploadAnswerSheetResponse(
        upload_id=str(upload.upload_id),
        presigned_url=presigned_url,
        expires_in=900  # 15 minutes
    )


@router.get("/exams/{exam_instance_id}/status", response_model=ExamStatusResponse)
async def get_exam_status(
    exam_instance_id: str,
    current_user: User = Depends(require_student),
    session: AsyncSession = Depends(get_session)
):
    """
    Get current status of an exam

    - Returns exam progress
    - Shows which parts are completed
    - Indicates if ready for submission
    """
    exam = await exam_service.get_exam_status(
        session,
        exam_instance_id,
        str(current_user.user_id)
    )

    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )

    # Calculate time remaining
    from datetime import datetime, timezone
    from sqlalchemy import select, func
    from models import AnswerSheetUpload

    time_remaining = None
    if exam.status in ['in_progress', 'submitted_mcq']:
        elapsed = (datetime.now(timezone.utc) - exam.started_at).total_seconds() / 60
        time_remaining = max(0, int(exam.duration_minutes - elapsed))

    # Count uploaded answer sheets
    upload_count_result = await session.execute(
        select(func.count()).select_from(AnswerSheetUpload).where(
            AnswerSheetUpload.exam_instance_id == exam_instance_id
        )
    )
    uploads_count = upload_count_result.scalar()

    # Determine if can submit (simplified - should check all required uploads)
    can_submit = exam.status == 'submitted_mcq' and uploads_count > 0

    return ExamStatusResponse(
        exam_instance_id=str(exam.exam_instance_id),
        status=exam.status,
        start_time=exam.started_at,
        time_remaining_minutes=time_remaining,
        mcq_submitted=(exam.status != 'in_progress'),
        answer_sheets_uploaded=uploads_count,
        total_answer_sheets_expected=0,  # Would calculate from exam config
        is_submitted=(exam.status in ['uploaded', 'pending_evaluation', 'evaluated']),
        can_submit=can_submit
    )


@router.get("/exams/history", response_model=List[ExamHistoryResponse])
async def get_exam_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(require_student),
    session: AsyncSession = Depends(get_session)
):
    """
    Get student's exam history

    - Returns list of past exams
    - Includes scores and status
    - Paginated results
    """
    exams, total = await exam_service.get_student_exam_history(
        session,
        str(current_user.user_id),
        limit,
        offset
    )

    history_responses = []
    for exam in exams:
        percentage = None
        if exam.total_score and exam.total_marks:
            percentage = round((exam.total_score / exam.total_marks) * 100, 2)

        history_responses.append(ExamHistoryResponse(
            exam_instance_id=str(exam.exam_instance_id),
            exam_type=exam.exam_type,
            status=exam.status,
            start_time=exam.started_at,
            end_time=exam.submitted_at,
            total_marks=exam.total_marks,
            mcq_score=exam.mcq_score,
            total_score=exam.total_score,
            percentage=percentage,
            evaluated_at=exam.submitted_at  # Simplified
        ))

    return history_responses
