"""
Question Service

Business logic for question bank management.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from typing import List, Optional, Tuple, Dict
from datetime import datetime, timezone
import uuid

from models import Question
from models.enums import QuestionType, QuestionDifficulty, QuestionStatus


class QuestionService:
    """Service for question bank operations"""

    @staticmethod
    async def create_question(
        session: AsyncSession,
        question_data: dict,
        created_by_user_id: str
    ) -> Question:
        """
        Create a new question

        Args:
            session: Database session
            question_data: Question details
            created_by_user_id: User ID of creator

        Returns:
            Created Question object
        """
        question = Question(
            question_type=question_data['question_type'],
            class_level=question_data['class_level'],
            unit=question_data['unit'],
            chapter=question_data.get('chapter'),
            topic=question_data.get('topic'),
            question_text=question_data['question_text'],
            question_image_url=question_data.get('question_image_url'),
            options=question_data.get('options'),
            correct_option=question_data.get('correct_option'),
            model_answer=question_data.get('model_answer'),
            marking_scheme=question_data.get('marking_scheme'),
            marks=question_data['marks'],
            difficulty=question_data.get('difficulty', QuestionDifficulty.MEDIUM.value),
            tags=question_data.get('tags', []),
            created_by_user_id=created_by_user_id,
            status=QuestionStatus.DRAFT.value,  # Start as draft
            version=1
        )

        session.add(question)
        await session.commit()
        await session.refresh(question)

        return question

    @staticmethod
    async def get_question_by_id(
        session: AsyncSession,
        question_id: str
    ) -> Optional[Question]:
        """
        Get question by ID

        Args:
            session: Database session
            question_id: Question UUID

        Returns:
            Question or None
        """
        return await session.get(Question, question_id)

    @staticmethod
    async def update_question(
        session: AsyncSession,
        question_id: str,
        update_data: dict,
        user_id: str
    ) -> Optional[Question]:
        """
        Update a question

        Args:
            session: Database session
            question_id: Question UUID
            update_data: Fields to update
            user_id: User making the update

        Returns:
            Updated Question or None
        """
        question = await session.get(Question, question_id)
        if not question:
            return None

        # Update fields
        for field, value in update_data.items():
            if value is not None and hasattr(question, field):
                setattr(question, field, value)

        # Increment version
        question.version += 1
        question.updated_at = datetime.now(timezone.utc)

        await session.commit()
        await session.refresh(question)

        return question

    @staticmethod
    async def delete_question(
        session: AsyncSession,
        question_id: str
    ) -> bool:
        """
        Soft delete a question (archive)

        Args:
            session: Database session
            question_id: Question UUID

        Returns:
            True if successful
        """
        question = await session.get(Question, question_id)
        if not question:
            return False

        question.status = QuestionStatus.ARCHIVED.value
        question.updated_at = datetime.now(timezone.utc)

        await session.commit()
        return True

    @staticmethod
    async def activate_question(
        session: AsyncSession,
        question_id: str
    ) -> Optional[Question]:
        """
        Activate a question (make it available for exams)

        Args:
            session: Database session
            question_id: Question UUID

        Returns:
            Updated Question or None
        """
        question = await session.get(Question, question_id)
        if not question:
            return None

        question.status = QuestionStatus.ACTIVE.value
        question.updated_at = datetime.now(timezone.utc)

        await session.commit()
        await session.refresh(question)

        return question

    @staticmethod
    async def search_questions(
        session: AsyncSession,
        filters: dict,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Question], int]:
        """
        Search questions with filters and pagination

        Args:
            session: Database session
            filters: Search criteria
            page: Page number (1-indexed)
            page_size: Results per page

        Returns:
            Tuple of (questions list, total count)
        """
        # Build query conditions
        conditions = []

        if filters.get('question_type'):
            conditions.append(Question.question_type == filters['question_type'])

        if filters.get('class_level'):
            conditions.append(Question.class_level == filters['class_level'])

        if filters.get('unit'):
            conditions.append(Question.unit == filters['unit'])

        if filters.get('chapter'):
            conditions.append(Question.chapter == filters['chapter'])

        if filters.get('difficulty'):
            conditions.append(Question.difficulty == filters['difficulty'])

        if filters.get('status'):
            conditions.append(Question.status == filters['status'])

        if filters.get('search_text'):
            search_term = f"%{filters['search_text']}%"
            conditions.append(Question.question_text.ilike(search_term))

        if filters.get('tags'):
            # Search for any of the provided tags
            for tag in filters['tags']:
                conditions.append(Question.tags.contains([tag]))

        # Build base query
        base_query = select(Question)
        if conditions:
            base_query = base_query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count()).select_from(Question)
        if conditions:
            count_query = count_query.where(and_(*conditions))

        count_result = await session.execute(count_query)
        total = count_result.scalar()

        # Get paginated results
        offset = (page - 1) * page_size
        query = base_query.order_by(Question.created_at.desc()).limit(page_size).offset(offset)

        result = await session.execute(query)
        questions = result.scalars().all()

        return questions, total

    @staticmethod
    async def get_question_stats(
        session: AsyncSession
    ) -> Dict:
        """
        Get statistics about question bank

        Args:
            session: Database session

        Returns:
            Dictionary with statistics
        """
        # Total questions
        total_result = await session.execute(
            select(func.count()).select_from(Question)
        )
        total_questions = total_result.scalar()

        # By type
        type_result = await session.execute(
            select(
                Question.question_type,
                func.count(Question.question_id)
            ).group_by(Question.question_type)
        )
        by_type = {row[0]: row[1] for row in type_result}

        # By class
        class_result = await session.execute(
            select(
                Question.class_level,
                func.count(Question.question_id)
            ).group_by(Question.class_level)
        )
        by_class = {row[0]: row[1] for row in class_result}

        # By status
        status_result = await session.execute(
            select(
                Question.status,
                func.count(Question.question_id)
            ).group_by(Question.status)
        )
        by_status = {row[0]: row[1] for row in status_result}

        # By difficulty
        difficulty_result = await session.execute(
            select(
                Question.difficulty,
                func.count(Question.question_id)
            ).group_by(Question.difficulty)
        )
        by_difficulty = {row[0]: row[1] for row in difficulty_result}

        # By unit (top 10)
        unit_result = await session.execute(
            select(
                Question.unit,
                func.count(Question.question_id)
            ).group_by(Question.unit)
            .order_by(func.count(Question.question_id).desc())
            .limit(10)
        )
        by_unit = {row[0]: row[1] for row in unit_result}

        return {
            'total_questions': total_questions,
            'by_type': by_type,
            'by_class': by_class,
            'by_unit': by_unit,
            'by_status': by_status,
            'by_difficulty': by_difficulty
        }

    @staticmethod
    async def clone_question(
        session: AsyncSession,
        question_id: str,
        user_id: str,
        modifications: Optional[dict] = None
    ) -> Optional[Question]:
        """
        Clone a question with optional modifications

        Args:
            session: Database session
            question_id: Question to clone
            user_id: User creating the clone
            modifications: Optional changes to make

        Returns:
            New Question or None
        """
        original = await session.get(Question, question_id)
        if not original:
            return None

        # Create copy
        cloned = Question(
            question_type=original.question_type,
            class_level=original.class_level,
            unit=original.unit,
            chapter=original.chapter,
            topic=original.topic,
            question_text=original.question_text,
            question_image_url=original.question_image_url,
            options=original.options.copy() if original.options else None,
            correct_option=original.correct_option,
            model_answer=original.model_answer,
            marking_scheme=original.marking_scheme,
            marks=original.marks,
            difficulty=original.difficulty,
            tags=original.tags.copy() if original.tags else [],
            created_by_user_id=user_id,
            status=QuestionStatus.DRAFT.value,
            version=1
        )

        # Apply modifications if provided
        if modifications:
            for field, value in modifications.items():
                if value is not None and hasattr(cloned, field):
                    setattr(cloned, field, value)

        session.add(cloned)
        await session.commit()
        await session.refresh(cloned)

        return cloned

    @staticmethod
    async def bulk_create_questions(
        session: AsyncSession,
        questions_data: List[dict],
        created_by_user_id: str
    ) -> Tuple[List[Question], List[dict]]:
        """
        Create multiple questions at once

        Args:
            session: Database session
            questions_data: List of question details
            created_by_user_id: User ID of creator

        Returns:
            Tuple of (created questions, errors)
        """
        created_questions = []
        errors = []

        for idx, q_data in enumerate(questions_data):
            try:
                question = Question(
                    question_type=q_data['question_type'],
                    class_level=q_data['class_level'],
                    unit=q_data['unit'],
                    chapter=q_data.get('chapter'),
                    topic=q_data.get('topic'),
                    question_text=q_data['question_text'],
                    question_image_url=q_data.get('question_image_url'),
                    options=q_data.get('options'),
                    correct_option=q_data.get('correct_option'),
                    model_answer=q_data.get('model_answer'),
                    marking_scheme=q_data.get('marking_scheme'),
                    marks=q_data['marks'],
                    difficulty=q_data.get('difficulty', QuestionDifficulty.MEDIUM.value),
                    tags=q_data.get('tags', []),
                    created_by_user_id=created_by_user_id,
                    status=QuestionStatus.DRAFT.value,
                    version=1
                )

                session.add(question)
                created_questions.append(question)

            except Exception as e:
                errors.append({
                    'index': idx,
                    'error': str(e),
                    'question_text': q_data.get('question_text', 'N/A')[:50]
                })

        if created_questions:
            await session.commit()
            for q in created_questions:
                await session.refresh(q)

        return created_questions, errors


# Global question service instance
question_service = QuestionService()
