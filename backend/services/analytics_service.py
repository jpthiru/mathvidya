"""
Analytics Service

Business logic for dashboards, reports, and performance analytics.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from collections import defaultdict

from models import (
    User, ExamInstance, QuestionMark, Evaluation,
    Question, Subscription
)
from models.enums import ExamStatus, UserRole, QuestionType


class AnalyticsService:
    """Service for analytics and reporting"""

    # ==================== Student Analytics ====================

    @staticmethod
    async def get_student_dashboard(
        session: AsyncSession,
        student_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive student dashboard

        Args:
            session: Database session
            student_id: Student user ID

        Returns:
            Dictionary with dashboard data
        """
        # Get student info
        student = await session.get(User, student_id)
        if not student:
            raise ValueError("Student not found")

        # Get all exams for student
        exams_result = await session.execute(
            select(ExamInstance).where(
                ExamInstance.student_user_id == student_id
            ).order_by(ExamInstance.created_at.desc())
        )
        exams = exams_result.scalars().all()

        total_exams = len(exams)
        exams_completed = sum(1 for e in exams if e.status in [
            ExamStatus.SUBMITTED_MCQ.value,
            ExamStatus.UPLOADED.value,
            ExamStatus.PENDING_EVALUATION.value,
            ExamStatus.EVALUATED.value
        ])
        exams_evaluated = sum(1 for e in exams if e.status == ExamStatus.EVALUATED.value)

        # Get evaluated exams for analysis
        evaluated_exams = [e for e in exams if e.status == ExamStatus.EVALUATED.value]

        # Overall percentage - calculate from all exams with scores
        overall_percentage = None
        exams_with_scores = [e for e in exams if e.mcq_score is not None or e.total_score is not None]
        if exams_with_scores:
            # Use percentage if available, otherwise calculate from scores
            total_percentage = 0
            count = 0
            for e in exams_with_scores:
                if e.percentage:
                    total_percentage += float(e.percentage)
                    count += 1
                elif e.total_marks and e.total_marks > 0:
                    score = float(e.total_score or e.mcq_score or 0)
                    total_percentage += (score / e.total_marks) * 100
                    count += 1
            if count > 0:
                overall_percentage = total_percentage / count

        # Recent exams (last 5 - all completed exams, not just evaluated)
        completed_exams = [e for e in exams if e.status not in [ExamStatus.CREATED.value, ExamStatus.IN_PROGRESS.value]]
        recent_exams = []
        for exam in completed_exams[:5]:
            recent_exams.append({
                'exam_instance_id': str(exam.exam_instance_id),
                'exam_type': exam.exam_type,
                'class_level': exam.class_level,
                'started_at': exam.started_at,
                'submitted_at': exam.submitted_at,
                'evaluated_at': exam.updated_at,
                'total_marks': exam.total_marks,
                'mcq_score': float(exam.mcq_score) if exam.mcq_score else 0,
                'manual_score': float(exam.manual_score) if exam.manual_score else 0,
                'total_score': float(exam.total_score) if exam.total_score else 0,
                'percentage': float(exam.percentage) if exam.percentage else 0,
                'status': exam.status,
                'time_taken_minutes': exam.time_taken_minutes
            })

        # Unit-wise performance
        unit_performance = await AnalyticsService._calculate_unit_performance(
            session, student_id, evaluated_exams
        )

        # Question type analysis
        question_type_analysis = await AnalyticsService._calculate_question_type_analysis(
            session, student_id, evaluated_exams
        )

        # Strength and weakness
        strength_weakness = AnalyticsService._identify_strengths_weaknesses(unit_performance)

        # Performance trend (last 10 exams)
        performance_trend = []
        for exam in evaluated_exams[:10]:
            performance_trend.append({
                'exam_instance_id': str(exam.exam_instance_id),
                'exam_date': exam.submitted_at or exam.created_at,
                'percentage': float(exam.percentage) if exam.percentage else 0,
                'total_score': float(exam.total_score) if exam.total_score else 0
            })

        # Board score prediction
        board_prediction = None
        if len(evaluated_exams) >= 3:
            board_prediction = AnalyticsService._predict_board_score(
                evaluated_exams, strength_weakness
            )

        # Calculate rank (if applicable)
        overall_rank = None
        total_students = None
        # TODO: Implement ranking logic based on subscription eligibility

        return {
            'student_id': str(student.user_id),
            'student_name': f"{student.first_name} {student.last_name}",
            'class_level': student.student_class,
            'total_exams': total_exams,
            'exams_completed': exams_completed,
            'exams_evaluated': exams_evaluated,
            'overall_percentage': overall_percentage,
            'overall_rank': overall_rank,
            'total_students': total_students,
            'recent_exams': recent_exams,
            'unit_performance': unit_performance,
            'question_type_analysis': question_type_analysis,
            'strength_weakness': strength_weakness,
            'performance_trend': performance_trend,
            'board_prediction': board_prediction
        }

    @staticmethod
    async def _calculate_unit_performance(
        session: AsyncSession,
        student_id: str,
        evaluated_exams: List[ExamInstance]
    ) -> List[Dict[str, Any]]:
        """Calculate performance by unit"""
        unit_data = defaultdict(lambda: {
            'total_questions': 0,
            'questions_attempted': 0,
            'questions_correct': 0,
            'total_marks': 0,
            'marks_obtained': 0,
            'mcq_correct': 0,
            'mcq_total': 0,
            'vsa_marks': 0,
            'vsa_total': 0,
            'sa_marks': 0,
            'sa_total': 0,
            'la_marks': 0,
            'la_total': 0,
            'easy_marks': 0,
            'easy_total': 0,
            'medium_marks': 0,
            'medium_total': 0,
            'hard_marks': 0,
            'hard_total': 0
        })

        for exam in evaluated_exams:
            # Get question marks for this exam
            marks_result = await session.execute(
                select(QuestionMark).where(
                    QuestionMark.exam_instance_id == str(exam.exam_instance_id)
                )
            )
            question_marks = marks_result.scalars().all()

            # Process each question
            questions = exam.exam_snapshot.get('questions', [])
            for q in questions:
                unit = q.get('question_content', {}).get('unit', 'Unknown')
                q_type = q.get('question_type')
                difficulty = q.get('question_content', {}).get('difficulty', 'medium')
                marks_possible = q.get('marks', 0)

                unit_data[unit]['total_questions'] += 1
                unit_data[unit]['total_marks'] += marks_possible

                # Find marks for this question
                q_mark = next(
                    (m for m in question_marks if m.question_number == q['question_number']),
                    None
                )

                if q_mark or q_type == 'MCQ':
                    unit_data[unit]['questions_attempted'] += 1

                    if q_type == 'MCQ':
                        # MCQ from exam_snapshot or student answers
                        # For now, use exam scores
                        unit_data[unit]['mcq_total'] += 1
                        # Simplified: assume proportional distribution
                    elif q_mark:
                        marks_obtained = float(q_mark.marks_awarded)
                        unit_data[unit]['marks_obtained'] += marks_obtained

                        if q_type == 'VSA':
                            unit_data[unit]['vsa_marks'] += marks_obtained
                            unit_data[unit]['vsa_total'] += marks_possible
                        elif q_type == 'SA':
                            unit_data[unit]['sa_marks'] += marks_obtained
                            unit_data[unit]['sa_total'] += marks_possible
                        elif q_type == 'LA':
                            unit_data[unit]['la_marks'] += marks_obtained
                            unit_data[unit]['la_total'] += marks_possible

                        # Difficulty tracking
                        if difficulty == 'easy':
                            unit_data[unit]['easy_marks'] += marks_obtained
                            unit_data[unit]['easy_total'] += marks_possible
                        elif difficulty == 'medium':
                            unit_data[unit]['medium_marks'] += marks_obtained
                            unit_data[unit]['medium_total'] += marks_possible
                        elif difficulty == 'hard':
                            unit_data[unit]['hard_marks'] += marks_obtained
                            unit_data[unit]['hard_total'] += marks_possible

        # Convert to list format
        unit_performance = []
        for unit, data in unit_data.items():
            percentage = 0
            if data['total_marks'] > 0:
                percentage = (data['marks_obtained'] / data['total_marks']) * 100

            easy_pct = None
            if data['easy_total'] > 0:
                easy_pct = (data['easy_marks'] / data['easy_total']) * 100

            medium_pct = None
            if data['medium_total'] > 0:
                medium_pct = (data['medium_marks'] / data['medium_total']) * 100

            hard_pct = None
            if data['hard_total'] > 0:
                hard_pct = (data['hard_marks'] / data['hard_total']) * 100

            unit_performance.append({
                'unit': unit,
                'total_questions': data['total_questions'],
                'questions_attempted': data['questions_attempted'],
                'questions_correct': data['questions_correct'],
                'total_marks': data['total_marks'],
                'marks_obtained': data['marks_obtained'],
                'percentage': round(percentage, 2),
                'mcq_correct': data['mcq_correct'],
                'mcq_total': data['mcq_total'],
                'vsa_marks': data['vsa_marks'],
                'vsa_total': data['vsa_total'],
                'sa_marks': data['sa_marks'],
                'sa_total': data['sa_total'],
                'la_marks': data['la_marks'],
                'la_total': data['la_total'],
                'easy_percentage': easy_pct,
                'medium_percentage': medium_pct,
                'hard_percentage': hard_pct
            })

        return sorted(unit_performance, key=lambda x: x['percentage'], reverse=True)

    @staticmethod
    async def _calculate_question_type_analysis(
        session: AsyncSession,
        student_id: str,
        evaluated_exams: List[ExamInstance]
    ) -> List[Dict[str, Any]]:
        """Calculate performance by question type"""
        type_data = defaultdict(lambda: {
            'total_questions': 0,
            'marks_possible': 0,
            'marks_obtained': 0
        })

        for exam in evaluated_exams:
            marks_result = await session.execute(
                select(QuestionMark).where(
                    QuestionMark.exam_instance_id == str(exam.exam_instance_id)
                )
            )
            question_marks = marks_result.scalars().all()

            questions = exam.exam_snapshot.get('questions', [])
            for q in questions:
                q_type = q.get('question_type')
                marks_possible = q.get('marks', 0)

                type_data[q_type]['total_questions'] += 1
                type_data[q_type]['marks_possible'] += marks_possible

                q_mark = next(
                    (m for m in question_marks if m.question_number == q['question_number']),
                    None
                )

                if q_mark:
                    type_data[q_type]['marks_obtained'] += float(q_mark.marks_awarded)

        # Convert to list
        analysis = []
        for q_type, data in type_data.items():
            percentage = 0
            if data['marks_possible'] > 0:
                percentage = (data['marks_obtained'] / data['marks_possible']) * 100

            avg_marks = 0
            if data['total_questions'] > 0:
                avg_marks = data['marks_obtained'] / data['total_questions']

            analysis.append({
                'question_type': q_type,
                'total_questions': data['total_questions'],
                'marks_possible': data['marks_possible'],
                'marks_obtained': data['marks_obtained'],
                'percentage': round(percentage, 2),
                'avg_marks_per_question': round(avg_marks, 2)
            })

        return analysis

    @staticmethod
    def _identify_strengths_weaknesses(
        unit_performance: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Identify strengths and weaknesses from unit performance"""
        strengths = []
        average = []
        weaknesses = []

        for unit in unit_performance:
            percentage = unit['percentage']
            topic_data = {
                'topic': unit['unit'],
                'unit': unit['unit'],
                'questions_attempted': unit['questions_attempted'],
                'percentage': percentage,
                'strength_level': ''
            }

            if percentage >= 75:
                topic_data['strength_level'] = 'strong'
                strengths.append(topic_data)
            elif percentage >= 50:
                topic_data['strength_level'] = 'average'
                average.append(topic_data)
            else:
                topic_data['strength_level'] = 'weak'
                weaknesses.append(topic_data)

        return {
            'strengths': strengths,
            'average': average,
            'weaknesses': weaknesses
        }

    @staticmethod
    def _predict_board_score(
        evaluated_exams: List[ExamInstance],
        strength_weakness: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict board exam score"""
        # Use last 5 exams for prediction
        recent_exams = evaluated_exams[:5]

        if not recent_exams:
            return None

        # Calculate recent average
        recent_percentages = [float(e.percentage) for e in recent_exams if e.percentage]
        recent_avg = sum(recent_percentages) / len(recent_percentages) if recent_percentages else 0

        # Calculate improvement rate
        improvement_rate = 0
        if len(recent_percentages) >= 2:
            old_avg = sum(recent_percentages[-2:]) / 2
            new_avg = sum(recent_percentages[:2]) / 2
            improvement_rate = new_avg - old_avg

        # Predicted percentage
        predicted = recent_avg + (improvement_rate * 0.5)  # Conservative prediction

        # Confidence level
        confidence = 'medium'
        if len(evaluated_exams) >= 10 and abs(improvement_rate) < 5:
            confidence = 'high'
        elif len(evaluated_exams) < 3:
            confidence = 'low'

        # Range
        min_predicted = max(0, predicted - 10)
        max_predicted = min(100, predicted + 10)

        # Focus areas from weaknesses
        focus_areas = [w['topic'] for w in strength_weakness.get('weaknesses', [])[:3]]

        return {
            'predicted_percentage': round(predicted, 2),
            'confidence_level': confidence,
            'recent_exam_avg': round(recent_avg, 2),
            'improvement_rate': round(improvement_rate, 2),
            'exams_analyzed': len(evaluated_exams),
            'min_predicted': round(min_predicted, 2),
            'max_predicted': round(max_predicted, 2),
            'focus_areas': focus_areas
        }

    # ==================== Teacher Analytics ====================

    @staticmethod
    async def get_teacher_dashboard(
        session: AsyncSession,
        teacher_id: str
    ) -> Dict[str, Any]:
        """Get teacher dashboard"""
        teacher = await session.get(User, teacher_id)
        if not teacher:
            raise ValueError("Teacher not found")

        # Get evaluations
        evals_result = await session.execute(
            select(Evaluation).where(
                Evaluation.teacher_user_id == teacher_id
            )
        )
        evaluations = evals_result.scalars().all()

        pending = sum(1 for e in evaluations if e.status == 'assigned')
        in_progress = sum(1 for e in evaluations if e.status == 'in_progress')
        overdue = sum(1 for e in evaluations if e.is_overdue())

        # Evaluation performance
        completed = [e for e in evaluations if e.status == 'completed']
        completed_on_time = sum(1 for e in completed if not e.sla_breached)
        completed_late = sum(1 for e in completed if e.sla_breached)

        avg_hours = 0
        if completed:
            total_hours = sum(
                (e.completed_at - e.assigned_at).total_seconds() / 3600
                for e in completed if e.completed_at and e.assigned_at
            )
            avg_hours = total_hours / len(completed) if len(completed) > 0 else 0

        sla_compliance = 0
        if len(completed) > 0:
            sla_compliance = (completed_on_time / len(completed)) * 100

        evaluation_performance = {
            'total_evaluations': len(evaluations),
            'completed_on_time': completed_on_time,
            'completed_late': completed_late,
            'pending': pending,
            'avg_completion_hours': round(avg_hours, 2),
            'sla_compliance_rate': round(sla_compliance, 2),
            'fastest_evaluation_hours': None,  # TODO
            'slowest_evaluation_hours': None   # TODO
        }

        # Questions created
        questions_result = await session.execute(
            select(func.count()).select_from(Question).where(
                Question.created_by_user_id == teacher_id
            )
        )
        questions_created = questions_result.scalar()

        active_questions_result = await session.execute(
            select(func.count()).select_from(Question).where(
                and_(
                    Question.created_by_user_id == teacher_id,
                    Question.status == 'active'
                )
            )
        )
        questions_active = active_questions_result.scalar()

        return {
            'teacher_id': str(teacher.user_id),
            'teacher_name': f"{teacher.first_name} {teacher.last_name}",
            'pending_evaluations': pending,
            'in_progress_evaluations': in_progress,
            'overdue_evaluations': overdue,
            'evaluation_performance': evaluation_performance,
            'class_performance': [],  # TODO: Calculate from evaluated exams
            'questions_created': questions_created,
            'questions_active': questions_active,
            'upcoming_deadlines': []  # TODO: Get from evaluation service
        }

    # ==================== Admin Analytics ====================

    @staticmethod
    async def get_admin_dashboard(
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Get admin dashboard"""
        # User counts
        users_result = await session.execute(select(func.count()).select_from(User))
        total_users = users_result.scalar()

        students_result = await session.execute(
            select(func.count()).select_from(User).where(User.role == UserRole.STUDENT.value)
        )
        total_students = students_result.scalar()

        teachers_result = await session.execute(
            select(func.count()).select_from(User).where(User.role == UserRole.TEACHER.value)
        )
        total_teachers = teachers_result.scalar()

        parents_result = await session.execute(
            select(func.count()).select_from(User).where(User.role == UserRole.PARENT.value)
        )
        total_parents = parents_result.scalar()

        # Exams
        exams_result = await session.execute(select(func.count()).select_from(ExamInstance))
        total_exams = exams_result.scalar()

        in_progress_result = await session.execute(
            select(func.count()).select_from(ExamInstance).where(
                ExamInstance.status == ExamStatus.IN_PROGRESS.value
            )
        )
        exams_in_progress = in_progress_result.scalar()

        pending_eval_result = await session.execute(
            select(func.count()).select_from(ExamInstance).where(
                ExamInstance.status.in_([
                    ExamStatus.UPLOADED.value,
                    ExamStatus.PENDING_EVALUATION.value
                ])
            )
        )
        exams_pending_evaluation = pending_eval_result.scalar()

        evaluated_result = await session.execute(
            select(func.count()).select_from(ExamInstance).where(
                ExamInstance.status == ExamStatus.EVALUATED.value
            )
        )
        exams_evaluated = evaluated_result.scalar()

        # Questions
        questions_result = await session.execute(select(func.count()).select_from(Question))
        total_questions = questions_result.scalar()

        active_questions_result = await session.execute(
            select(func.count()).select_from(Question).where(Question.status == 'active')
        )
        active_questions = active_questions_result.scalar()

        system_overview = {
            'total_users': total_users,
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_parents': total_parents,
            'active_subscriptions': 0,  # TODO: Implement subscription tracking
            'total_exams': total_exams,
            'exams_in_progress': exams_in_progress,
            'exams_pending_evaluation': exams_pending_evaluation,
            'exams_evaluated': exams_evaluated,
            'total_questions': total_questions,
            'active_questions': active_questions
        }

        # Overall average percentage
        evaluated_exams_result = await session.execute(
            select(ExamInstance).where(
                ExamInstance.status == ExamStatus.EVALUATED.value
            )
        )
        evaluated_exams = evaluated_exams_result.scalars().all()

        overall_avg = 0
        if evaluated_exams:
            total_pct = sum(float(e.percentage) for e in evaluated_exams if e.percentage)
            overall_avg = total_pct / len(evaluated_exams)

        # SLA compliance from evaluation service stats
        # TODO: Get from evaluation service

        return {
            'system_overview': system_overview,
            'subscription_breakdown': [],
            'overall_avg_percentage': round(overall_avg, 2),
            'class_performance': [],
            'sla_compliance': {
                'total_evaluations': 0,
                'on_time': 0,
                'breached': 0,
                'compliance_rate': 0,
                'avg_completion_hours': 0
            },
            'popular_units': [],
            'top_teachers': [],
            'recent_registrations': 0,
            'recent_exams': 0
        }

    # ==================== Leaderboard ====================

    @staticmethod
    async def get_leaderboard(
        session: AsyncSession,
        class_level: str,
        period: str = 'all-time',
        current_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get leaderboard (Top 10)

        Args:
            session: Database session
            class_level: Class level (X or XII)
            period: monthly, quarterly, all-time
            current_user_id: Optional current user to show their rank

        Returns:
            Leaderboard data
        """
        # Get all students in class with evaluated exams
        students_result = await session.execute(
            select(User).where(
                and_(
                    User.role == UserRole.STUDENT.value,
                    User.student_class == class_level
                )
            )
        )
        students = students_result.scalars().all()

        # Calculate average for each student
        student_stats = []
        for student in students:
            exams_result = await session.execute(
                select(ExamInstance).where(
                    and_(
                        ExamInstance.student_user_id == str(student.user_id),
                        ExamInstance.status == ExamStatus.EVALUATED.value
                    )
                )
            )
            exams = exams_result.scalars().all()

            if not exams:
                continue

            total_exams = len(exams)
            total_score = sum(float(e.total_score) for e in exams if e.total_score)
            avg_percentage = sum(float(e.percentage) for e in exams if e.percentage) / total_exams

            student_stats.append({
                'student_id': str(student.user_id),
                'student_name': f"{student.first_name} {student.last_name}",
                'class_level': class_level,
                'total_exams': total_exams,
                'avg_percentage': avg_percentage,
                'total_score': total_score
            })

        # Sort by average percentage
        student_stats.sort(key=lambda x: x['avg_percentage'], reverse=True)

        # Top 10
        top_10 = []
        for idx, stats in enumerate(student_stats[:10], start=1):
            badge = None
            if idx == 1:
                badge = 'gold'
            elif idx == 2:
                badge = 'silver'
            elif idx == 3:
                badge = 'bronze'

            top_10.append({
                'rank': idx,
                'student_id': stats['student_id'],
                'student_name': stats['student_name'],
                'class_level': stats['class_level'],
                'total_exams': stats['total_exams'],
                'avg_percentage': round(stats['avg_percentage'], 2),
                'total_score': round(stats['total_score'], 2),
                'badge': badge
            })

        # Find current user rank if provided
        current_user_rank = None
        current_user_entry = None
        if current_user_id:
            for idx, stats in enumerate(student_stats, start=1):
                if stats['student_id'] == current_user_id:
                    current_user_rank = idx
                    if idx > 10:  # Not in top 10
                        current_user_entry = {
                            'rank': idx,
                            'student_id': stats['student_id'],
                            'student_name': stats['student_name'],
                            'class_level': stats['class_level'],
                            'total_exams': stats['total_exams'],
                            'avg_percentage': round(stats['avg_percentage'], 2),
                            'total_score': round(stats['total_score'], 2),
                            'badge': None
                        }
                    break

        return {
            'class_level': class_level,
            'period': period,
            'entries': top_10,
            'current_user_rank': current_user_rank,
            'current_user_entry': current_user_entry,
            'eligibility_criteria': 'Premium and Centum plan subscribers only',
            'last_updated': datetime.now(timezone.utc)
        }


# Global analytics service instance
analytics_service = AnalyticsService()
