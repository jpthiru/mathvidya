"""
Evaluation Service

Business logic for teacher evaluation workflow.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from typing import List, Optional, Tuple, Dict
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid

from models import Evaluation, QuestionMark, ExamInstance, User
from models.enums import EvaluationStatus, ExamStatus, QuestionType


class EvaluationService:
    """Service for teacher evaluation operations"""

    @staticmethod
    def calculate_sla_deadline(
        assigned_at: datetime,
        sla_hours: int,
        exclude_sundays: bool = True
    ) -> datetime:
        """
        Calculate SLA deadline excluding Sundays and holidays

        Args:
            assigned_at: Assignment timestamp
            sla_hours: Hours allocated (24 or 48)
            exclude_sundays: Whether to skip Sundays

        Returns:
            SLA deadline datetime
        """
        current = assigned_at
        hours_remaining = sla_hours

        while hours_remaining > 0:
            # Move forward by 1 hour
            current = current + timedelta(hours=1)

            # Skip Sundays if enabled
            if exclude_sundays and current.weekday() == 6:  # Sunday
                continue

            hours_remaining -= 1

        return current

    @staticmethod
    async def assign_evaluation(
        session: AsyncSession,
        exam_instance_id: str,
        teacher_user_id: str,
        sla_hours: int
    ) -> Evaluation:
        """
        Assign an exam to a teacher for evaluation

        Args:
            session: Database session
            exam_instance_id: Exam to evaluate
            teacher_user_id: Teacher to assign
            sla_hours: SLA hours (24 or 48)

        Returns:
            Created Evaluation object
        """
        # Verify exam exists and is submitted
        exam = await session.get(ExamInstance, exam_instance_id)
        if not exam:
            raise ValueError("Exam instance not found")

        if exam.status != ExamStatus.SUBMITTED:
            raise ValueError("Exam must be submitted before evaluation assignment")

        # Verify teacher exists
        teacher = await session.get(User, teacher_user_id)
        if not teacher or teacher.role not in ['teacher', 'admin']:
            raise ValueError("Invalid teacher user")

        # Check if evaluation already exists
        existing = await session.execute(
            select(Evaluation).where(Evaluation.exam_instance_id == exam_instance_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Evaluation already assigned for this exam")

        # Calculate SLA deadline
        assigned_at = datetime.now(timezone.utc)
        sla_deadline = EvaluationService.calculate_sla_deadline(
            assigned_at,
            sla_hours
        )

        # Create evaluation
        evaluation = Evaluation(
            exam_instance_id=exam_instance_id,
            teacher_user_id=teacher_user_id,
            assigned_at=assigned_at,
            sla_deadline=sla_deadline,
            sla_hours_allocated=sla_hours,
            status=EvaluationStatus.ASSIGNED.value
        )

        session.add(evaluation)

        # Update exam status
        exam.status = ExamStatus.UNDER_EVALUATION.value

        await session.commit()
        await session.refresh(evaluation)

        return evaluation

    @staticmethod
    async def start_evaluation(
        session: AsyncSession,
        evaluation_id: str,
        teacher_user_id: str
    ) -> Evaluation:
        """
        Teacher starts working on evaluation

        Args:
            session: Database session
            evaluation_id: Evaluation to start
            teacher_user_id: Teacher performing evaluation

        Returns:
            Updated Evaluation
        """
        evaluation = await session.get(Evaluation, evaluation_id)
        if not evaluation:
            raise ValueError("Evaluation not found")

        # Verify teacher ownership
        if str(evaluation.teacher_user_id) != teacher_user_id:
            raise ValueError("Evaluation assigned to different teacher")

        if evaluation.status != EvaluationStatus.ASSIGNED.value:
            raise ValueError("Evaluation already started or completed")

        # Update status
        evaluation.status = EvaluationStatus.IN_PROGRESS.value
        evaluation.started_at = datetime.now(timezone.utc)

        await session.commit()
        await session.refresh(evaluation)

        return evaluation

    @staticmethod
    async def submit_question_marks(
        session: AsyncSession,
        evaluation_id: str,
        teacher_user_id: str,
        marks_data: List[dict],
        annotation_data: Optional[dict] = None
    ) -> Tuple[Evaluation, List[QuestionMark]]:
        """
        Submit marks for one or more questions

        Args:
            session: Database session
            evaluation_id: Evaluation ID
            teacher_user_id: Teacher submitting marks
            marks_data: List of {question_number, marks_awarded, teacher_comment}
            annotation_data: Optional annotation data

        Returns:
            Tuple of (Updated Evaluation, List of QuestionMark objects)
        """
        evaluation = await session.get(Evaluation, evaluation_id)
        if not evaluation:
            raise ValueError("Evaluation not found")

        # Verify teacher ownership
        if str(evaluation.teacher_user_id) != teacher_user_id:
            raise ValueError("Evaluation assigned to different teacher")

        if evaluation.status == EvaluationStatus.COMPLETED.value:
            raise ValueError("Evaluation already completed")

        # Start evaluation if not started
        if evaluation.status == EvaluationStatus.ASSIGNED.value:
            evaluation.status = EvaluationStatus.IN_PROGRESS.value
            evaluation.started_at = datetime.now(timezone.utc)

        # Get exam instance for question details
        exam = await session.get(ExamInstance, str(evaluation.exam_instance_id))
        if not exam:
            raise ValueError("Exam instance not found")

        questions_snapshot = exam.exam_snapshot.get('questions', [])
        question_map = {q['question_number']: q for q in questions_snapshot}

        created_marks = []

        for mark_data in marks_data:
            question_number = mark_data['question_number']

            # Get question details from snapshot
            question_info = question_map.get(question_number)
            if not question_info:
                raise ValueError(f"Question {question_number} not found in exam")

            # Validate marks don't exceed possible
            marks_possible = Decimal(str(question_info['marks']))
            marks_awarded = Decimal(str(mark_data['marks_awarded']))

            if marks_awarded > marks_possible:
                raise ValueError(
                    f"Marks awarded ({marks_awarded}) cannot exceed "
                    f"marks possible ({marks_possible}) for question {question_number}"
                )

            # Check if marks already exist for this question
            existing = await session.execute(
                select(QuestionMark).where(
                    and_(
                        QuestionMark.evaluation_id == evaluation_id,
                        QuestionMark.question_number == question_number
                    )
                )
            )
            existing_mark = existing.scalar_one_or_none()

            if existing_mark:
                # Update existing
                existing_mark.marks_awarded = marks_awarded
                existing_mark.teacher_comment = mark_data.get('teacher_comment')
                created_marks.append(existing_mark)
            else:
                # Create new
                question_mark = QuestionMark(
                    evaluation_id=evaluation_id,
                    exam_instance_id=str(evaluation.exam_instance_id),
                    question_number=question_number,
                    question_id=question_info['question_id'],
                    question_type=question_info['question_type'],
                    unit=question_info.get('question_content', {}).get('unit'),
                    marks_awarded=marks_awarded,
                    marks_possible=marks_possible,
                    teacher_comment=mark_data.get('teacher_comment')
                )
                session.add(question_mark)
                created_marks.append(question_mark)

        # Update annotation data if provided
        if annotation_data:
            if evaluation.annotation_data:
                # Merge with existing
                existing_annotations = evaluation.annotation_data
                existing_annotations.update(annotation_data)
                evaluation.annotation_data = existing_annotations
            else:
                evaluation.annotation_data = annotation_data

        evaluation.updated_at = datetime.now(timezone.utc)

        await session.commit()

        for mark in created_marks:
            await session.refresh(mark)
        await session.refresh(evaluation)

        return evaluation, created_marks

    @staticmethod
    async def complete_evaluation(
        session: AsyncSession,
        evaluation_id: str,
        teacher_user_id: str
    ) -> Evaluation:
        """
        Complete the evaluation (finalize)

        Args:
            session: Database session
            evaluation_id: Evaluation to complete
            teacher_user_id: Teacher completing evaluation

        Returns:
            Completed Evaluation
        """
        evaluation = await session.get(Evaluation, evaluation_id)
        if not evaluation:
            raise ValueError("Evaluation not found")

        # Verify teacher ownership
        if str(evaluation.teacher_user_id) != teacher_user_id:
            raise ValueError("Evaluation assigned to different teacher")

        if evaluation.status == EvaluationStatus.COMPLETED.value:
            raise ValueError("Evaluation already completed")

        # Get exam instance
        exam = await session.get(ExamInstance, str(evaluation.exam_instance_id))
        if not exam:
            raise ValueError("Exam instance not found")

        # Get all question marks for this evaluation
        marks_result = await session.execute(
            select(QuestionMark).where(
                QuestionMark.evaluation_id == evaluation_id
            )
        )
        question_marks = marks_result.scalars().all()

        # Get total questions requiring manual evaluation
        questions_snapshot = exam.exam_snapshot.get('questions', [])
        manual_questions = [
            q for q in questions_snapshot
            if q['question_type'] in ['VSA', 'SA', 'LA']
        ]

        # Verify all manual questions are evaluated
        if len(question_marks) < len(manual_questions):
            raise ValueError(
                f"Not all questions evaluated. "
                f"Expected {len(manual_questions)}, got {len(question_marks)}"
            )

        # Calculate total manual marks
        total_manual = sum(float(mark.marks_awarded) for mark in question_marks)

        # Update evaluation
        evaluation.status = EvaluationStatus.COMPLETED.value
        evaluation.completed_at = datetime.now(timezone.utc)
        evaluation.total_manual_marks = Decimal(str(total_manual))

        # Check if SLA breached
        if datetime.now(timezone.utc) > evaluation.sla_deadline:
            evaluation.sla_breached = True

        # Update exam scores
        exam.manual_score = Decimal(str(total_manual))
        exam.total_score = exam.mcq_score + exam.manual_score

        if exam.total_marks > 0:
            exam.percentage = (exam.total_score / Decimal(str(exam.total_marks))) * 100

        exam.status = ExamStatus.EVALUATED.value

        await session.commit()
        await session.refresh(evaluation)

        return evaluation

    @staticmethod
    async def get_evaluation_by_id(
        session: AsyncSession,
        evaluation_id: str
    ) -> Optional[Evaluation]:
        """Get evaluation by ID"""
        return await session.get(Evaluation, evaluation_id)

    @staticmethod
    async def get_teacher_pending_evaluations(
        session: AsyncSession,
        teacher_user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Evaluation], int]:
        """
        Get pending evaluations for a teacher

        Args:
            session: Database session
            teacher_user_id: Teacher's user ID
            page: Page number (1-indexed)
            page_size: Results per page

        Returns:
            Tuple of (evaluations list, total count)
        """
        # Build query
        base_query = select(Evaluation).where(
            and_(
                Evaluation.teacher_user_id == teacher_user_id,
                Evaluation.status.in_([
                    EvaluationStatus.ASSIGNED.value,
                    EvaluationStatus.IN_PROGRESS.value
                ])
            )
        )

        # Get total count
        count_query = select(func.count()).select_from(Evaluation).where(
            and_(
                Evaluation.teacher_user_id == teacher_user_id,
                Evaluation.status.in_([
                    EvaluationStatus.ASSIGNED.value,
                    EvaluationStatus.IN_PROGRESS.value
                ])
            )
        )

        count_result = await session.execute(count_query)
        total = count_result.scalar()

        # Get paginated results ordered by SLA deadline
        offset = (page - 1) * page_size
        query = base_query.order_by(Evaluation.sla_deadline.asc()).limit(page_size).offset(offset)

        result = await session.execute(query)
        evaluations = result.scalars().all()

        return evaluations, total

    @staticmethod
    async def get_evaluation_progress(
        session: AsyncSession,
        evaluation_id: str
    ) -> Dict:
        """
        Get current evaluation progress

        Args:
            session: Database session
            evaluation_id: Evaluation ID

        Returns:
            Dictionary with progress information
        """
        evaluation = await session.get(Evaluation, evaluation_id)
        if not evaluation:
            raise ValueError("Evaluation not found")

        # Get exam instance
        exam = await session.get(ExamInstance, str(evaluation.exam_instance_id))
        if not exam:
            raise ValueError("Exam instance not found")

        # Get questions requiring manual evaluation
        questions_snapshot = exam.exam_snapshot.get('questions', [])
        manual_questions = [
            q for q in questions_snapshot
            if q['question_type'] in ['VSA', 'SA', 'LA']
        ]

        # Get evaluated questions
        marks_result = await session.execute(
            select(QuestionMark).where(
                QuestionMark.evaluation_id == evaluation_id
            ).order_by(QuestionMark.question_number)
        )
        question_marks = marks_result.scalars().all()

        # Calculate totals
        total_questions = len(manual_questions)
        questions_evaluated = len(question_marks)
        questions_remaining = total_questions - questions_evaluated

        total_possible_marks = sum(q['marks'] for q in manual_questions)
        marks_awarded = sum(float(mark.marks_awarded) for mark in question_marks)

        current_percentage = None
        if total_possible_marks > 0:
            current_percentage = (marks_awarded / total_possible_marks) * 100

        return {
            'evaluation_id': str(evaluation.evaluation_id),
            'status': evaluation.status,
            'total_questions': total_questions,
            'questions_evaluated': questions_evaluated,
            'questions_remaining': questions_remaining,
            'total_possible_marks': float(total_possible_marks),
            'marks_awarded': marks_awarded,
            'current_percentage': current_percentage,
            'question_marks': question_marks,
            'sla_deadline': evaluation.sla_deadline,
            'is_overdue': evaluation.is_overdue()
        }

    @staticmethod
    async def get_teacher_workload(
        session: AsyncSession,
        teacher_user_id: str
    ) -> Dict:
        """
        Get teacher's current workload statistics

        Args:
            session: Database session
            teacher_user_id: Teacher's user ID

        Returns:
            Dictionary with workload stats
        """
        # Get all evaluations for teacher
        result = await session.execute(
            select(Evaluation).where(
                Evaluation.teacher_user_id == teacher_user_id
            )
        )
        evaluations = result.scalars().all()

        total_assigned = len(evaluations)
        pending_count = sum(1 for e in evaluations if e.status == EvaluationStatus.ASSIGNED.value)
        in_progress_count = sum(1 for e in evaluations if e.status == EvaluationStatus.IN_PROGRESS.value)
        completed_count = sum(1 for e in evaluations if e.status == EvaluationStatus.COMPLETED.value)

        overdue_count = sum(1 for e in evaluations if e.is_overdue())
        sla_breached_count = sum(1 for e in evaluations if e.sla_breached)

        # Get upcoming deadlines (next 5)
        upcoming = sorted(
            [e for e in evaluations if e.status != EvaluationStatus.COMPLETED.value],
            key=lambda x: x.sla_deadline
        )[:5]

        upcoming_deadlines = [
            {
                'evaluation_id': str(e.evaluation_id),
                'exam_instance_id': str(e.exam_instance_id),
                'sla_deadline': e.sla_deadline,
                'is_overdue': e.is_overdue()
            }
            for e in upcoming
        ]

        return {
            'total_assigned': total_assigned,
            'pending_count': pending_count,
            'in_progress_count': in_progress_count,
            'completed_count': completed_count,
            'overdue_count': overdue_count,
            'sla_breached_count': sla_breached_count,
            'upcoming_deadlines': upcoming_deadlines
        }

    @staticmethod
    async def get_evaluation_stats(
        session: AsyncSession
    ) -> Dict:
        """
        Get system-wide evaluation statistics

        Args:
            session: Database session

        Returns:
            Dictionary with statistics
        """
        # Total evaluations
        total_result = await session.execute(
            select(func.count()).select_from(Evaluation)
        )
        total_evaluations = total_result.scalar()

        # By status
        assigned_result = await session.execute(
            select(func.count()).select_from(Evaluation).where(
                Evaluation.status == EvaluationStatus.ASSIGNED.value
            )
        )
        assigned_count = assigned_result.scalar()

        in_progress_result = await session.execute(
            select(func.count()).select_from(Evaluation).where(
                Evaluation.status == EvaluationStatus.IN_PROGRESS.value
            )
        )
        in_progress_count = in_progress_result.scalar()

        completed_result = await session.execute(
            select(func.count()).select_from(Evaluation).where(
                Evaluation.status == EvaluationStatus.COMPLETED.value
            )
        )
        completed_count = completed_result.scalar()

        # Get all evaluations for SLA calculations
        all_evals_result = await session.execute(select(Evaluation))
        all_evals = all_evals_result.scalars().all()

        total_overdue = sum(1 for e in all_evals if e.is_overdue())
        total_sla_breached = sum(1 for e in all_evals if e.sla_breached)

        sla_compliance_rate = 0.0
        if total_evaluations > 0:
            sla_compliance_rate = ((total_evaluations - total_sla_breached) / total_evaluations) * 100

        # Average completion time
        completed_evals = [e for e in all_evals if e.status == EvaluationStatus.COMPLETED.value and e.completed_at and e.assigned_at]
        avg_completion_time_hours = None
        if completed_evals:
            total_hours = sum(
                (e.completed_at - e.assigned_at).total_seconds() / 3600
                for e in completed_evals
            )
            avg_completion_time_hours = total_hours / len(completed_evals)

        return {
            'total_evaluations': total_evaluations,
            'assigned_count': assigned_count,
            'in_progress_count': in_progress_count,
            'completed_count': completed_count,
            'total_overdue': total_overdue,
            'total_sla_breached': total_sla_breached,
            'sla_compliance_rate': sla_compliance_rate,
            'avg_completion_time_hours': avg_completion_time_hours
        }


# Global evaluation service instance
evaluation_service = EvaluationService()
