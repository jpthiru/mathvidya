"""
Models Package

Import all models for Alembic autodiscovery and application use.
"""

# Enums
from models.enums import (
    UserRole,
    RelationshipType,
    PlanType,
    SubscriptionStatus,
    QuestionType,
    QuestionDifficulty,
    QuestionStatus,
    ExamType,
    ExamStatus,
    EvaluationStatus,
)

# User and Mapping
from models.user import User
from models.mapping import ParentStudentMapping

# Subscription
from models.subscription import SubscriptionPlan, Subscription

# Question Bank
from models.question import Question

# Exam System
from models.exam_template import ExamTemplate
from models.exam_instance import (
    ExamInstance,
    StudentMCQAnswer,
    AnswerSheetUpload,
    UnansweredQuestion,
)

# Evaluation
from models.evaluation import Evaluation, QuestionMark

# System
from models.system import AuditLog, Holiday, SystemConfig

# Notifications
from models.notification import Notification, NotificationPreference

# Export all models
__all__ = [
    # Enums
    "UserRole",
    "RelationshipType",
    "PlanType",
    "SubscriptionStatus",
    "QuestionType",
    "QuestionDifficulty",
    "QuestionStatus",
    "ExamType",
    "ExamStatus",
    "EvaluationStatus",
    # Models
    "User",
    "ParentStudentMapping",
    "SubscriptionPlan",
    "Subscription",
    "Question",
    "ExamTemplate",
    "ExamInstance",
    "StudentMCQAnswer",
    "AnswerSheetUpload",
    "UnansweredQuestion",
    "Evaluation",
    "QuestionMark",
    "AuditLog",
    "Holiday",
    "SystemConfig",
    "Notification",
    "NotificationPreference",
]
