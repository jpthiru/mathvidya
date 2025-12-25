"""
Celery Application Configuration

Initialize Celery for background task processing.
"""

from celery import Celery
from celery.schedules import crontab
from config.settings import settings

# Create Celery app
celery_app = Celery(
    "mathvidya",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["tasks.sla_tasks", "tasks.analytics_tasks"]  # Import task modules
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",  # IST timezone
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Task routes (priority queues)
celery_app.conf.task_routes = {
    "tasks.sla_tasks.assign_teacher_to_evaluation": {"queue": "evaluation", "priority": 9},
    "tasks.sla_tasks.detect_sla_breaches": {"queue": "evaluation", "priority": 9},
    "tasks.analytics_tasks.refresh_leaderboard": {"queue": "analytics", "priority": 3},
    "tasks.analytics_tasks.aggregate_daily_stats": {"queue": "analytics", "priority": 3},
}

# Periodic tasks (Celery Beat schedule)
celery_app.conf.beat_schedule = {
    # Check for SLA breaches every 15 minutes
    "detect-sla-breaches": {
        "task": "tasks.sla_tasks.detect_sla_breaches",
        "schedule": crontab(minute="*/15"),
    },
    # Refresh leaderboard every hour
    "refresh-leaderboard": {
        "task": "tasks.analytics_tasks.refresh_leaderboard",
        "schedule": crontab(minute=0, hour="*"),
    },
    # Aggregate daily stats at 1 AM
    "aggregate-daily-stats": {
        "task": "tasks.analytics_tasks.aggregate_daily_stats",
        "schedule": crontab(minute=0, hour=1),
    },
    # Reset monthly subscription counters on 1st of each month
    "reset-monthly-counters": {
        "task": "tasks.subscription_tasks.reset_monthly_counters",
        "schedule": crontab(minute=0, hour=0, day_of_month=1),
    },
}


if __name__ == "__main__":
    celery_app.start()
