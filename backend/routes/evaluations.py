"""
Evaluation Routes

API endpoints for teacher evaluation workflow.
Accessible by teachers and admins.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import math

from database import get_session
from models import User, Evaluation, ExamInstance
from dependencies.auth import require_teacher_or_admin, require_teacher, require_admin
from schemas.evaluation import (
    StartEvaluationRequest,
    SubmitMarksRequest,
    CompleteEvaluationRequest,
    EvaluationDetailResponse,
    EvaluationSummaryResponse,
    EvaluationListResponse,
    QuestionMarkResponse,
    EvaluationProgressResponse,
    AssignEvaluationRequest,
    AssignEvaluationResponse,
    PendingEvaluationFilterRequest,
    TeacherWorkloadResponse,
    EvaluationStatsResponse,
    UploadAnnotatedImageRequest,
    UploadAnnotatedImageResponse,
    BulkAssignEvaluationsRequest,
    BulkAssignEvaluationsResponse
)
from services import evaluation_service, s3_service


router = APIRouter()


@router.post("/evaluations/assign", response_model=AssignEvaluationResponse, status_code=status.HTTP_201_CREATED)
async def assign_evaluation(
    request: AssignEvaluationRequest,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Assign an exam to a teacher for evaluation (Admin only)

    - **exam_instance_id**: Exam that needs evaluation
    - **teacher_user_id**: Teacher to assign
    - **sla_hours**: SLA hours (24 for Centum, 48 for others)

    **Permissions**: Admins only
    """
    try:
        evaluation = await evaluation_service.assign_evaluation(
            session,
            request.exam_instance_id,
            request.teacher_user_id,
            request.sla_hours
        )

        return AssignEvaluationResponse(
            evaluation_id=str(evaluation.evaluation_id),
            exam_instance_id=str(evaluation.exam_instance_id),
            teacher_user_id=str(evaluation.teacher_user_id),
            sla_deadline=evaluation.sla_deadline,
            status=evaluation.status
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/evaluations/assign-bulk", response_model=BulkAssignEvaluationsResponse)
async def bulk_assign_evaluations(
    request: BulkAssignEvaluationsRequest,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Bulk assign multiple evaluations (Admin only)

    - Maximum 50 assignments per request
    - Partial success: some may succeed even if others fail
    - Returns list of errors for failed assignments

    **Permissions**: Admins only
    """
    assignments_data = [a.dict() for a in request.assignments]

    created = []
    errors = []

    for idx, assign_data in enumerate(assignments_data):
        try:
            evaluation = await evaluation_service.assign_evaluation(
                session,
                assign_data['exam_instance_id'],
                assign_data['teacher_user_id'],
                assign_data['sla_hours']
            )
            created.append(evaluation)

        except Exception as e:
            errors.append({
                'index': idx,
                'error': str(e),
                'exam_instance_id': assign_data.get('exam_instance_id', 'N/A')
            })

    return BulkAssignEvaluationsResponse(
        total_submitted=len(assignments_data),
        successful=len(created),
        failed=len(errors),
        errors=errors,
        created_evaluation_ids=[str(e.evaluation_id) for e in created]
    )


@router.get("/evaluations/my-pending", response_model=EvaluationListResponse)
async def get_my_pending_evaluations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    current_user: User = Depends(require_teacher),
    session: AsyncSession = Depends(get_session)
):
    """
    Get my pending evaluations (Teacher only)

    - Returns evaluations assigned or in-progress
    - Ordered by SLA deadline (most urgent first)
    - Shows SLA status and overdue flag

    **Permissions**: Teachers only
    """
    evaluations, total = await evaluation_service.get_teacher_pending_evaluations(
        session,
        str(current_user.user_id),
        page,
        page_size
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    # Get exam and student info for each evaluation
    summaries = []
    for evaluation in evaluations:
        exam = await session.get(ExamInstance, str(evaluation.exam_instance_id))
        student = await session.get(User, str(exam.student_user_id))

        summaries.append(EvaluationSummaryResponse(
            evaluation_id=str(evaluation.evaluation_id),
            exam_instance_id=str(evaluation.exam_instance_id),
            student_name=f"{student.first_name} {student.last_name}",
            exam_type=exam.exam_type,
            class_level=exam.class_level,
            total_marks=exam.total_marks,
            status=evaluation.status,
            assigned_at=evaluation.assigned_at,
            sla_deadline=evaluation.sla_deadline,
            sla_breached=evaluation.sla_breached,
            is_overdue=evaluation.is_overdue(),
            started_at=evaluation.started_at,
            completed_at=evaluation.completed_at
        ))

    return EvaluationListResponse(
        evaluations=summaries,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationDetailResponse)
async def get_evaluation(
    evaluation_id: str,
    current_user: User = Depends(require_teacher_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Get evaluation details

    - Full evaluation information
    - Exam and student details
    - SLA tracking

    **Permissions**: Teachers and Admins
    """
    evaluation = await evaluation_service.get_evaluation_by_id(session, evaluation_id)

    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found"
        )

    # Teachers can only view their own evaluations
    if current_user.role == 'teacher' and str(evaluation.teacher_user_id) != str(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get exam and student info
    exam = await session.get(ExamInstance, str(evaluation.exam_instance_id))
    student = await session.get(User, str(exam.student_user_id))

    exam_info = {
        'exam_type': exam.exam_type,
        'class_level': exam.class_level,
        'total_marks': exam.total_marks,
        'started_at': exam.started_at,
        'submitted_at': exam.submitted_at
    }

    student_info = {
        'student_id': str(student.user_id),
        'name': f"{student.first_name} {student.last_name}",
        'email': student.email
    }

    return EvaluationDetailResponse(
        evaluation_id=str(evaluation.evaluation_id),
        exam_instance_id=str(evaluation.exam_instance_id),
        teacher_user_id=str(evaluation.teacher_user_id),
        assigned_at=evaluation.assigned_at,
        sla_deadline=evaluation.sla_deadline,
        sla_hours_allocated=evaluation.sla_hours_allocated,
        sla_breached=evaluation.sla_breached,
        is_overdue=evaluation.is_overdue(),
        status=evaluation.status,
        started_at=evaluation.started_at,
        completed_at=evaluation.completed_at,
        total_manual_marks=float(evaluation.total_manual_marks) if evaluation.total_manual_marks else None,
        exam_info=exam_info,
        student_info=student_info,
        created_at=evaluation.created_at,
        updated_at=evaluation.updated_at
    )


@router.post("/evaluations/{evaluation_id}/start", response_model=EvaluationDetailResponse)
async def start_evaluation(
    evaluation_id: str,
    current_user: User = Depends(require_teacher),
    session: AsyncSession = Depends(get_session)
):
    """
    Start evaluation (Teacher only)

    - Changes status from ASSIGNED to IN_PROGRESS
    - Records start time
    - Only assigned teacher can start

    **Permissions**: Teachers only (assigned teacher)
    """
    try:
        evaluation = await evaluation_service.start_evaluation(
            session,
            evaluation_id,
            str(current_user.user_id)
        )

        # Get exam and student info
        exam = await session.get(ExamInstance, str(evaluation.exam_instance_id))
        student = await session.get(User, str(exam.student_user_id))

        exam_info = {
            'exam_type': exam.exam_type,
            'class_level': exam.class_level,
            'total_marks': exam.total_marks
        }

        student_info = {
            'student_id': str(student.user_id),
            'name': f"{student.first_name} {student.last_name}"
        }

        return EvaluationDetailResponse(
            evaluation_id=str(evaluation.evaluation_id),
            exam_instance_id=str(evaluation.exam_instance_id),
            teacher_user_id=str(evaluation.teacher_user_id),
            assigned_at=evaluation.assigned_at,
            sla_deadline=evaluation.sla_deadline,
            sla_hours_allocated=evaluation.sla_hours_allocated,
            sla_breached=evaluation.sla_breached,
            is_overdue=evaluation.is_overdue(),
            status=evaluation.status,
            started_at=evaluation.started_at,
            completed_at=evaluation.completed_at,
            total_manual_marks=float(evaluation.total_manual_marks) if evaluation.total_manual_marks else None,
            exam_info=exam_info,
            student_info=student_info,
            created_at=evaluation.created_at,
            updated_at=evaluation.updated_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/evaluations/{evaluation_id}/submit-marks", response_model=EvaluationProgressResponse)
async def submit_question_marks(
    evaluation_id: str,
    request: SubmitMarksRequest,
    current_user: User = Depends(require_teacher),
    session: AsyncSession = Depends(get_session)
):
    """
    Submit marks for one or more questions (Teacher only)

    - Can submit partial marks (doesn't complete evaluation)
    - Updates existing marks if question already evaluated
    - Optional annotation data for answer sheets
    - Validates marks don't exceed possible marks

    **Permissions**: Teachers only (assigned teacher)
    """
    try:
        marks_data = [m.dict() for m in request.question_marks]

        # Convert annotations to dict if provided
        annotation_data = None
        if request.annotations:
            annotation_data = {
                'pages': [a.dict() for a in request.annotations]
            }

        evaluation, question_marks = await evaluation_service.submit_question_marks(
            session,
            evaluation_id,
            str(current_user.user_id),
            marks_data,
            annotation_data
        )

        # Get progress information
        progress = await evaluation_service.get_evaluation_progress(session, evaluation_id)

        # Convert question marks to response format
        marks_responses = [
            QuestionMarkResponse(
                mark_id=str(mark.mark_id),
                evaluation_id=str(mark.evaluation_id),
                question_number=mark.question_number,
                question_id=str(mark.question_id),
                question_type=mark.question_type,
                unit=mark.unit,
                marks_awarded=float(mark.marks_awarded),
                marks_possible=float(mark.marks_possible),
                percentage=mark.get_percentage(),
                teacher_comment=mark.teacher_comment,
                created_at=mark.created_at
            )
            for mark in progress['question_marks']
        ]

        return EvaluationProgressResponse(
            evaluation_id=progress['evaluation_id'],
            status=progress['status'],
            total_questions=progress['total_questions'],
            questions_evaluated=progress['questions_evaluated'],
            questions_remaining=progress['questions_remaining'],
            total_possible_marks=progress['total_possible_marks'],
            marks_awarded=progress['marks_awarded'],
            current_percentage=progress['current_percentage'],
            question_marks=marks_responses,
            sla_deadline=progress['sla_deadline'],
            is_overdue=progress['is_overdue']
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/evaluations/{evaluation_id}/complete", response_model=EvaluationDetailResponse)
async def complete_evaluation(
    evaluation_id: str,
    request: Optional[CompleteEvaluationRequest] = None,
    current_user: User = Depends(require_teacher),
    session: AsyncSession = Depends(get_session)
):
    """
    Complete evaluation (finalize) (Teacher only)

    - Marks evaluation as COMPLETED
    - Updates exam status to EVALUATED
    - Calculates final scores
    - Checks if SLA was met
    - Requires all manual questions to be evaluated

    **Permissions**: Teachers only (assigned teacher)
    """
    try:
        evaluation = await evaluation_service.complete_evaluation(
            session,
            evaluation_id,
            str(current_user.user_id)
        )

        # Get exam and student info
        exam = await session.get(ExamInstance, str(evaluation.exam_instance_id))
        student = await session.get(User, str(exam.student_user_id))

        exam_info = {
            'exam_type': exam.exam_type,
            'class_level': exam.class_level,
            'total_marks': exam.total_marks,
            'total_score': float(exam.total_score),
            'percentage': float(exam.percentage) if exam.percentage else None
        }

        student_info = {
            'student_id': str(student.user_id),
            'name': f"{student.first_name} {student.last_name}"
        }

        return EvaluationDetailResponse(
            evaluation_id=str(evaluation.evaluation_id),
            exam_instance_id=str(evaluation.exam_instance_id),
            teacher_user_id=str(evaluation.teacher_user_id),
            assigned_at=evaluation.assigned_at,
            sla_deadline=evaluation.sla_deadline,
            sla_hours_allocated=evaluation.sla_hours_allocated,
            sla_breached=evaluation.sla_breached,
            is_overdue=evaluation.is_overdue(),
            status=evaluation.status,
            started_at=evaluation.started_at,
            completed_at=evaluation.completed_at,
            total_manual_marks=float(evaluation.total_manual_marks) if evaluation.total_manual_marks else None,
            exam_info=exam_info,
            student_info=student_info,
            created_at=evaluation.created_at,
            updated_at=evaluation.updated_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/evaluations/{evaluation_id}/progress", response_model=EvaluationProgressResponse)
async def get_evaluation_progress(
    evaluation_id: str,
    current_user: User = Depends(require_teacher_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Get evaluation progress

    - Shows how many questions evaluated
    - Current marks awarded
    - Remaining questions
    - SLA status

    **Permissions**: Teachers and Admins
    """
    try:
        evaluation = await evaluation_service.get_evaluation_by_id(session, evaluation_id)

        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation not found"
            )

        # Teachers can only view their own evaluations
        if current_user.role == 'teacher' and str(evaluation.teacher_user_id) != str(current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        progress = await evaluation_service.get_evaluation_progress(session, evaluation_id)

        # Convert question marks to response format
        marks_responses = [
            QuestionMarkResponse(
                mark_id=str(mark.mark_id),
                evaluation_id=str(mark.evaluation_id),
                question_number=mark.question_number,
                question_id=str(mark.question_id),
                question_type=mark.question_type,
                unit=mark.unit,
                marks_awarded=float(mark.marks_awarded),
                marks_possible=float(mark.marks_possible),
                percentage=mark.get_percentage(),
                teacher_comment=mark.teacher_comment,
                created_at=mark.created_at
            )
            for mark in progress['question_marks']
        ]

        return EvaluationProgressResponse(
            evaluation_id=progress['evaluation_id'],
            status=progress['status'],
            total_questions=progress['total_questions'],
            questions_evaluated=progress['questions_evaluated'],
            questions_remaining=progress['questions_remaining'],
            total_possible_marks=progress['total_possible_marks'],
            marks_awarded=progress['marks_awarded'],
            current_percentage=progress['current_percentage'],
            question_marks=marks_responses,
            sla_deadline=progress['sla_deadline'],
            is_overdue=progress['is_overdue']
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/evaluations/teacher/workload", response_model=TeacherWorkloadResponse)
async def get_my_workload(
    current_user: User = Depends(require_teacher),
    session: AsyncSession = Depends(get_session)
):
    """
    Get my current workload (Teacher only)

    - Total evaluations assigned
    - Pending, in-progress, completed counts
    - Overdue and SLA breach counts
    - Next 5 upcoming deadlines

    **Permissions**: Teachers only
    """
    workload = await evaluation_service.get_teacher_workload(
        session,
        str(current_user.user_id)
    )

    return TeacherWorkloadResponse(
        teacher_user_id=str(current_user.user_id),
        teacher_name=f"{current_user.first_name} {current_user.last_name}",
        total_assigned=workload['total_assigned'],
        pending_count=workload['pending_count'],
        in_progress_count=workload['in_progress_count'],
        completed_count=workload['completed_count'],
        overdue_count=workload['overdue_count'],
        sla_breached_count=workload['sla_breached_count'],
        upcoming_deadlines=workload['upcoming_deadlines']
    )


@router.get("/evaluations/stats/overview", response_model=EvaluationStatsResponse)
async def get_evaluation_stats(
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Get system-wide evaluation statistics (Admin only)

    - Total evaluations count
    - Breakdown by status
    - SLA compliance metrics
    - Average completion time

    **Permissions**: Admins only
    """
    stats = await evaluation_service.get_evaluation_stats(session)

    return EvaluationStatsResponse(
        total_evaluations=stats['total_evaluations'],
        assigned_count=stats['assigned_count'],
        in_progress_count=stats['in_progress_count'],
        completed_count=stats['completed_count'],
        total_overdue=stats['total_overdue'],
        total_sla_breached=stats['total_sla_breached'],
        sla_compliance_rate=stats['sla_compliance_rate'],
        avg_completion_time_hours=stats['avg_completion_time_hours']
    )


@router.post("/evaluations/{evaluation_id}/upload-annotated-image", response_model=UploadAnnotatedImageResponse)
async def get_annotated_image_upload_url(
    evaluation_id: str,
    request: UploadAnnotatedImageRequest,
    current_user: User = Depends(require_teacher),
    session: AsyncSession = Depends(get_session)
):
    """
    Get presigned URL for uploading annotated answer sheet image (Teacher only)

    - Teacher annotations stored in S3
    - Supports tick/cross/half stamps
    - Returns URL valid for 15 minutes

    **Permissions**: Teachers only (assigned teacher)
    """
    # Verify evaluation exists and belongs to teacher
    evaluation = await evaluation_service.get_evaluation_by_id(session, evaluation_id)

    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found"
        )

    if str(evaluation.teacher_user_id) != str(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Generate S3 key
    file_extension = request.file_name.split('.')[-1] if '.' in request.file_name else 'jpg'
    s3_key = f"teacher-annotations/{evaluation_id}/page_{request.page_number}.{file_extension}"

    # Generate presigned URL
    presigned_url = s3_service.generate_presigned_upload_url(s3_key)

    if not presigned_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate upload URL"
        )

    return UploadAnnotatedImageResponse(
        evaluation_id=evaluation_id,
        page_number=request.page_number,
        presigned_url=presigned_url,
        s3_key=s3_key,
        expires_in=900
    )
