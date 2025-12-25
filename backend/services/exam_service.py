"""
Exam Service

Business logic for exam operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional, Tuple
from datetime import datetime, timedelta, timezone
import uuid
import random

from models import (
    ExamTemplate,
    ExamInstance,
    Question,
    StudentMCQAnswer,
    AnswerSheetUpload,
    UnansweredQuestion,
    User,
    Subscription
)
from models.enums import ExamType, ExamStatus, QuestionType, QuestionStatus


class ExamService:
    """Service for exam-related operations"""

    @staticmethod
    async def get_available_templates(
        session: AsyncSession,
        class_level: str
    ) -> List[ExamTemplate]:
        """
        Get available exam templates for a class

        Args:
            session: Database session
            class_level: Student's class (X or XII)

        Returns:
            List of active exam templates
        """
        result = await session.execute(
            select(ExamTemplate).where(
                and_(
                    ExamTemplate.class_level == class_level,
                    ExamTemplate.is_active == True
                )
            ).order_by(ExamTemplate.template_name)
        )
        return result.scalars().all()

    @staticmethod
    async def start_exam(
        session: AsyncSession,
        student_id: str,
        template_id: str
    ) -> Tuple[ExamInstance, List[Question]]:
        """
        Start a new exam instance

        Args:
            session: Database session
            student_id: Student's user ID
            template_id: Exam template ID

        Returns:
            Tuple of (ExamInstance, List of Questions)

        Raises:
            ValueError: If template not found or student has active exam
        """
        # Check for active exams
        result = await session.execute(
            select(ExamInstance).where(
                and_(
                    ExamInstance.student_user_id == student_id,
                    ExamInstance.status.in_([
                        ExamStatus.CREATED.value,
                        ExamStatus.IN_PROGRESS.value
                    ])
                )
            )
        )
        active_exam = result.scalar_one_or_none()
        if active_exam:
            raise ValueError("You already have an active exam in progress")

        # Get template
        template = await session.get(ExamTemplate, template_id)
        if not template or not template.is_active:
            raise ValueError("Exam template not found or inactive")

        # Generate questions based on section_config
        questions = await ExamService._generate_exam_questions(
            session,
            template.class_level,
            template.get_sections()
        )

        if not questions:
            raise ValueError("Could not generate exam questions")

        # Create exam instance
        exam_instance = ExamInstance(
            student_user_id=student_id,
            template_id=template_id,
            exam_type=template.exam_type,
            class_level=template.class_level,
            total_marks=template.get_total_marks(),
            duration_minutes=template.get_duration_minutes(),
            started_at=datetime.now(timezone.utc),
            status=ExamStatus.IN_PROGRESS.value,
            exam_snapshot=template.config  # Store config snapshot
        )

        session.add(exam_instance)
        await session.flush()  # Get exam_instance_id

        # Store question mapping in snapshot
        question_ids = [str(q.question_id) for q in questions]
        if exam_instance.exam_snapshot is None:
            exam_instance.exam_snapshot = {}
        exam_instance.exam_snapshot['question_ids'] = question_ids

        await session.commit()
        await session.refresh(exam_instance)

        return exam_instance, questions

    @staticmethod
    async def _generate_exam_questions(
        session: AsyncSession,
        class_level: str,
        sections: list
    ) -> List[Question]:
        """
        Generate exam questions based on section configuration

        Args:
            session: Database session
            class_level: Class level (X or XII)
            sections: List of section configurations from template
                      Each section: {"type": "MCQ", "count": 20, "marks_each": 1}

        Returns:
            List of selected questions
        """
        all_questions = []

        # Iterate through sections (MCQ, VSA, SA, LA)
        for section in sections:
            question_count = section.get('count', 0)
            question_type = section.get('type')
            marks_per_question = section.get('marks_each', section.get('marks_per_question', 1))

            if question_count == 0:
                continue

            # Query questions of this type
            result = await session.execute(
                select(Question).where(
                    and_(
                        Question.class_level == class_level,
                        Question.question_type == question_type,
                        Question.marks == marks_per_question,
                        Question.status == QuestionStatus.ACTIVE.value
                    )
                )
            )
            available_questions = result.scalars().all()

            if len(available_questions) < question_count:
                # Not enough questions available, take what we have
                all_questions.extend(available_questions)
                continue

            # Randomly select questions
            selected = random.sample(available_questions, question_count)
            all_questions.extend(selected)

        return all_questions

    @staticmethod
    async def submit_mcq_answers(
        session: AsyncSession,
        exam_instance_id: str,
        student_id: str,
        answers: List[dict]
    ) -> Tuple[int, int, float]:
        """
        Submit MCQ answers and calculate score

        Args:
            session: Database session
            exam_instance_id: Exam instance ID
            student_id: Student ID
            answers: List of {"question_id": ..., "selected_option": ...}

        Returns:
            Tuple of (total_questions, correct_count, score)

        Raises:
            ValueError: If exam not found or not in correct status
        """
        # Get exam instance
        exam = await session.get(ExamInstance, exam_instance_id)
        if not exam or str(exam.student_user_id) != student_id:
            raise ValueError("Exam not found")

        if exam.status != ExamStatus.IN_PROGRESS.value:
            raise ValueError("Exam is not in progress")

        # Store MCQ answers and calculate score
        correct_count = 0
        total_mcq = len(answers)

        for idx, answer_data in enumerate(answers, 1):
            question_id = answer_data['question_id']
            selected_option = answer_data['selected_option']

            # Get question to check correct answer
            question = await session.get(Question, question_id)
            if not question:
                continue

            is_correct = question.correct_option == selected_option

            if is_correct:
                correct_count += 1

            # Save answer - use correct column names from model
            mcq_answer = StudentMCQAnswer(
                exam_instance_id=exam_instance_id,
                question_number=idx,
                question_id=question_id,
                selected_choices=[selected_option],  # JSONB array format
                is_correct=is_correct,
                marks_awarded=question.marks if is_correct else 0,
                marks_possible=question.marks
            )
            session.add(mcq_answer)

        # Update exam status
        exam.status = ExamStatus.SUBMITTED_MCQ.value
        exam.mcq_score = correct_count * 1  # Assuming 1 mark per MCQ

        await session.commit()

        return total_mcq, correct_count, exam.mcq_score

    @staticmethod
    async def get_exam_status(
        session: AsyncSession,
        exam_instance_id: str,
        student_id: str
    ) -> Optional[ExamInstance]:
        """
        Get exam instance status

        Args:
            session: Database session
            exam_instance_id: Exam instance ID
            student_id: Student ID

        Returns:
            ExamInstance or None
        """
        result = await session.execute(
            select(ExamInstance).where(
                and_(
                    ExamInstance.exam_instance_id == exam_instance_id,
                    ExamInstance.student_user_id == student_id
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_student_exam_history(
        session: AsyncSession,
        student_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[ExamInstance], int]:
        """
        Get student's exam history

        Args:
            session: Database session
            student_id: Student ID
            limit: Number of results
            offset: Pagination offset

        Returns:
            Tuple of (exams list, total count)
        """
        # Get total count
        count_result = await session.execute(
            select(func.count()).select_from(ExamInstance).where(
                ExamInstance.student_user_id == student_id
            )
        )
        total = count_result.scalar()

        # Get exams
        result = await session.execute(
            select(ExamInstance).where(
                ExamInstance.student_user_id == student_id
            ).order_by(ExamInstance.start_time.desc())
            .limit(limit).offset(offset)
        )
        exams = result.scalars().all()

        return exams, total


# Global exam service instance
exam_service = ExamService()
