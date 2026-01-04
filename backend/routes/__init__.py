"""Routes module - API endpoints"""

from . import auth, exams, questions, evaluations, analytics, subscriptions, notifications, teacher, admin, promo, site_feedback

__all__ = [
    "auth",
    "exams",
    "questions",
    "evaluations",
    "analytics",
    "subscriptions",
    "notifications",
    "teacher",
    "admin",
    "promo",
    "site_feedback"
]
