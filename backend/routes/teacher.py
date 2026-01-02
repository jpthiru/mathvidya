"""
Teacher Routes

API endpoints for teacher-specific operations including student management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import Optional
import logging

from database import get_session
from models import User, ExamInstance, Evaluation, Question
from models.enums import UserRole, ExamStatus, EvaluationStatus
from dependencies.auth import require_teacher, require_teacher_or_admin
from schemas.teacher import (
    StudentListResponse,
    StudentListItem,
    StudentSearchFilters,
    StudentExamsResponse,
    StudentExamListItem,
    TeacherStudentStats,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Student Management ====================

@router.get("/students", response_model=StudentListResponse)
async def get_students(
    search: Optional[str] = Query(None, description="Search by email or name"),
    student_class: Optional[str] = Query(None, pattern="^(X|XII)$"),
    has_exams: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_teacher_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Get list of students with performance summary.

    Teachers can view all students and their basic performance metrics.
    Supports filtering by class, search, and exam status.

    **Permissions**: Teachers and Admins
    """
    # Build base query for students
    query = select(User).where(User.role == UserRole.STUDENT.value)

    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                User.email.ilike(search_pattern),
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern)
            )
        )

    if student_class:
        query = query.where(User.student_class == student_class)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Calculate pagination
    total_pages = (total + page_size - 1) // page_size
    offset = (page - 1) * page_size

    # Get students with pagination
    query = query.order_by(desc(User.created_at)).offset(offset).limit(page_size)
    result = await session.execute(query)
    students = result.scalars().all()

    # Build response with performance data
    student_items = []
    for student in students:
        # Get exam stats for this student
        exam_stats_query = select(
            func.count(ExamInstance.exam_instance_id).label('total_exams'),
            func.count(ExamInstance.total_score).filter(ExamInstance.total_score.isnot(None)).label('evaluated'),
            func.avg(
                (ExamInstance.total_score / ExamInstance.total_marks * 100)
            ).filter(ExamInstance.total_score.isnot(None)).label('avg_percentage'),
            func.max(ExamInstance.started_at).label('last_exam')
        ).where(ExamInstance.student_user_id == student.user_id)

        stats_result = await session.execute(exam_stats_query)
        stats = stats_result.first()

        # Filter by has_exams if specified
        if has_exams is True and (stats.total_exams or 0) == 0:
            continue
        if has_exams is False and (stats.total_exams or 0) > 0:
            continue

        student_items.append(StudentListItem(
            student_id=str(student.user_id),
            email=student.email,
            first_name=student.first_name,
            last_name=student.last_name,
            full_name=f"{student.first_name} {student.last_name}",
            student_class=student.student_class or "Unknown",
            school_name=student.school_name,
            total_exams=stats.total_exams or 0,
            exams_evaluated=stats.evaluated or 0,
            average_percentage=float(stats.avg_percentage) if stats.avg_percentage else None,
            last_exam_date=stats.last_exam,
            is_active=student.is_active,
            created_at=student.created_at
        ))

    return StudentListResponse(
        students=student_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/students/stats", response_model=TeacherStudentStats)
async def get_student_stats(
    current_user: User = Depends(require_teacher_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Get statistics about students for teacher dashboard.

    **Permissions**: Teachers and Admins
    """
    # Total students count by class
    class_counts = await session.execute(
        select(
            User.student_class,
            func.count(User.user_id)
        ).where(User.role == UserRole.STUDENT.value)
        .group_by(User.student_class)
    )
    class_data = {row[0]: row[1] for row in class_counts.all()}

    total_students = sum(class_data.values())
    class_x = class_data.get('X', 0)
    class_xii = class_data.get('XII', 0)

    # Students who have taken exams
    students_with_exams_result = await session.execute(
        select(func.count(func.distinct(ExamInstance.student_user_id)))
    )
    students_with_exams = students_with_exams_result.scalar() or 0

    # Total exams
    total_exams_result = await session.execute(
        select(func.count(ExamInstance.exam_instance_id))
    )
    total_exams = total_exams_result.scalar() or 0

    # Pending evaluations
    pending_evals_result = await session.execute(
        select(func.count(Evaluation.evaluation_id)).where(
            Evaluation.status.in_([EvaluationStatus.ASSIGNED.value, EvaluationStatus.IN_PROGRESS.value])
        )
    )
    pending_evaluations = pending_evals_result.scalar() or 0

    # Average student percentage (from evaluated exams)
    avg_result = await session.execute(
        select(func.avg(ExamInstance.total_score / ExamInstance.total_marks * 100)).where(
            and_(
                ExamInstance.total_score.isnot(None),
                ExamInstance.total_marks > 0
            )
        )
    )
    avg_percentage = avg_result.scalar()

    # Top performers (avg > 75%) and struggling students (avg < 40%)
    # This is a simplified calculation - getting students with their averages
    student_avgs_query = select(
        ExamInstance.student_user_id,
        func.avg(ExamInstance.total_score / ExamInstance.total_marks * 100).label('avg')
    ).where(
        and_(
            ExamInstance.total_score.isnot(None),
            ExamInstance.total_marks > 0
        )
    ).group_by(ExamInstance.student_user_id)

    student_avgs = await session.execute(student_avgs_query)
    avgs = student_avgs.all()

    top_performers = sum(1 for _, avg in avgs if avg and avg >= 75)
    struggling = sum(1 for _, avg in avgs if avg and avg < 40)

    return TeacherStudentStats(
        total_students=total_students,
        students_with_exams=students_with_exams,
        total_exams_taken=total_exams,
        exams_pending_evaluation=pending_evaluations,
        class_x_students=class_x,
        class_xii_students=class_xii,
        avg_student_percentage=float(avg_percentage) if avg_percentage else None,
        top_performers=top_performers,
        struggling_students=struggling
    )


@router.get("/students/{student_id}/exams", response_model=StudentExamsResponse)
async def get_student_exams(
    student_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_teacher_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Get list of exams for a specific student.

    **Permissions**: Teachers and Admins
    """
    # Verify student exists
    student_result = await session.execute(
        select(User).where(
            and_(
                User.user_id == student_id,
                User.role == UserRole.STUDENT.value
            )
        )
    )
    student = student_result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Count total exams
    count_result = await session.execute(
        select(func.count(ExamInstance.exam_instance_id)).where(
            ExamInstance.student_user_id == student_id
        )
    )
    total = count_result.scalar() or 0

    # Get exams with pagination
    offset = (page - 1) * page_size
    exams_query = select(ExamInstance).where(
        ExamInstance.student_user_id == student_id
    ).order_by(desc(ExamInstance.started_at)).offset(offset).limit(page_size)

    exams_result = await session.execute(exams_query)
    exams = exams_result.scalars().all()

    # Build exam list
    exam_items = []
    for exam in exams:
        # Get evaluation info if exists
        eval_result = await session.execute(
            select(Evaluation).where(Evaluation.exam_instance_id == exam.exam_instance_id)
        )
        evaluation = eval_result.scalar_one_or_none()

        # Get teacher name if evaluated
        evaluated_by = None
        if evaluation and evaluation.teacher_user_id:
            teacher_result = await session.execute(
                select(User.first_name, User.last_name).where(
                    User.user_id == evaluation.teacher_user_id
                )
            )
            teacher = teacher_result.first()
            if teacher:
                evaluated_by = f"{teacher.first_name} {teacher.last_name}"

        # Calculate percentage
        percentage = None
        if exam.total_score is not None and exam.total_marks > 0:
            percentage = (float(exam.total_score) / exam.total_marks) * 100

        # Extract question counts from exam_snapshot
        snapshot = exam.exam_snapshot or {}
        questions = snapshot.get('questions', [])
        total_questions = len(questions)
        mcq_count = sum(1 for q in questions if q.get('question_type') == 'MCQ')
        vsa_count = sum(1 for q in questions if q.get('question_type') == 'VSA')
        sa_count = sum(1 for q in questions if q.get('question_type') == 'SA')

        exam_items.append(StudentExamListItem(
            exam_instance_id=str(exam.exam_instance_id),
            exam_type=exam.exam_type,
            started_at=exam.started_at,
            submitted_at=exam.submitted_at,
            evaluated_at=evaluation.completed_at if evaluation else None,
            status=exam.status,
            total_marks=exam.total_marks,
            mcq_score=float(exam.mcq_score) if exam.mcq_score else None,
            total_score=float(exam.total_score) if exam.total_score else None,
            percentage=percentage,
            total_questions=total_questions,
            mcq_count=mcq_count,
            vsa_count=vsa_count,
            sa_count=sa_count,
            evaluation_id=str(evaluation.evaluation_id) if evaluation else None,
            evaluated_by=evaluated_by
        ))

    return StudentExamsResponse(
        student_id=str(student.user_id),
        student_name=f"{student.first_name} {student.last_name}",
        student_class=student.student_class or "Unknown",
        exams=exam_items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/exams/{exam_instance_id}/results")
async def get_student_exam_results(
    exam_instance_id: str,
    current_user: User = Depends(require_teacher_or_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Get detailed exam results for a student's exam.

    Teachers can view any student's exam results with question-by-question breakdown.

    **Permissions**: Teachers and Admins
    """
    # Get exam instance
    exam = await session.get(ExamInstance, exam_instance_id)
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )

    # Get student info
    student = await session.get(User, exam.student_user_id)
    student_name = f"{student.first_name} {student.last_name}" if student else "Unknown Student"

    # Get exam snapshot with question IDs and answers
    snapshot = exam.exam_snapshot or {}
    question_ids = snapshot.get('question_ids', [])
    student_answers = snapshot.get('student_answers', {})

    # Load questions
    questions = []
    mcq_answers = []
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

            # Build question data
            question_data = {
                "question_id": str(question.question_id),
                "question_number": idx,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "options": question.options,
                "correct_option": question.correct_option,
                "correct_answer": question.correct_option,  # For frontend compatibility
                "marks": question.marks,
                "unit": question.unit,
                "student_answer": student_answer,
                "is_correct": is_correct,
                "model_answer": question.model_answer,
                "marking_scheme": question.marking_scheme
            }
            questions.append(question_data)

            # Build MCQ answer data for frontend compatibility
            if student_answer is not None:
                mcq_answers.append({
                    "question_number": idx,
                    "selected_choices": [student_answer] if student_answer else [],
                    "is_correct": is_correct
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
        "student_name": student_name,
        "started_at": exam.started_at.isoformat() if exam.started_at else None,
        "submitted_at": exam.submitted_at.isoformat() if exam.submitted_at else None,
        "total_marks": exam.total_marks,
        "mcq_score": float(exam.mcq_score) if exam.mcq_score else 0,
        "total_score": float(exam.total_score) if exam.total_score else 0,
        "percentage": (exam.total_score / exam.total_marks * 100) if exam.total_marks and exam.total_score else 0,
        "total_questions": len(questions),
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "unanswered_count": unanswered_count,
        "time_taken_minutes": time_taken_minutes,
        "questions": questions,
        "mcq_answers": mcq_answers,  # For frontend compatibility
        "answers": student_answers
    }
