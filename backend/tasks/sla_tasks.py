"""
SLA-related Celery Tasks

Background tasks for SLA monitoring and teacher assignment.
"""

from celery import shared_task
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def assign_teacher_to_evaluation(self, evaluation_id: str, plan_type: str):
    """
    Assign a teacher to an evaluation with SLA deadline calculation.

    This task is triggered when a student submits their answer sheets.

    Args:
        evaluation_id: UUID of the evaluation
        plan_type: Subscription plan type (centum, premium, basic, etc.)
    """
    try:
        logger.info(f"Assigning teacher to evaluation {evaluation_id}")

        # TODO: Implement actual teacher assignment logic
        # from services.teacher_assignment import assign_teacher
        # assign_teacher(evaluation_id, plan_type)

        logger.info(f"Successfully assigned teacher to evaluation {evaluation_id}")

    except Exception as exc:
        logger.error(f"Error assigning teacher: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def detect_sla_breaches():
    """
    Detect evaluations that have breached their SLA deadline.

    Runs every 15 minutes via Celery Beat.
    Marks evaluations as breached and notifies admins.
    """
    try:
        logger.info("Starting SLA breach detection")

        # TODO: Implement SLA breach detection logic
        # from services.sla_service import detect_breaches
        # breached_evaluations = detect_breaches()

        # for eval_id in breached_evaluations:
        #     notify_admin_of_breach(eval_id)

        logger.info("SLA breach detection completed")

    except Exception as exc:
        logger.error(f"Error in SLA breach detection: {exc}")
        raise


@shared_task
def calculate_sla_deadline(submission_time: str, sla_hours: int):
    """
    Calculate SLA deadline excluding weekends and holidays.

    Args:
        submission_time: ISO format timestamp
        sla_hours: SLA duration in working hours

    Returns:
        ISO format timestamp of deadline
    """
    try:
        # TODO: Implement SLA deadline calculation
        # from services.sla_service import calculate_deadline
        # deadline = calculate_deadline(submission_time, sla_hours)
        # return deadline.isoformat()

        pass

    except Exception as exc:
        logger.error(f"Error calculating SLA deadline: {exc}")
        raise


@shared_task
def notify_teacher_of_assignment(teacher_id: str, evaluation_id: str):
    """
    Notify teacher of new evaluation assignment.

    Args:
        teacher_id: UUID of the teacher
        evaluation_id: UUID of the evaluation
    """
    try:
        logger.info(f"Notifying teacher {teacher_id} of evaluation {evaluation_id}")

        # TODO: Implement notification logic (email/SMS)
        # from services.notification_service import notify_teacher
        # notify_teacher(teacher_id, evaluation_id)

    except Exception as exc:
        logger.error(f"Error notifying teacher: {exc}")
        # Don't retry notification failures
        pass
