"""
Centralized Enumerations

All enum types used across Mathvidya models.
"""

import enum


class UserRole(str, enum.Enum):
    """User role enumeration"""
    STUDENT = "student"
    PARENT = "parent"
    TEACHER = "teacher"
    ADMIN = "admin"


class RelationshipType(str, enum.Enum):
    """Parent-student relationship types"""
    FATHER = "father"
    MOTHER = "mother"
    GUARDIAN = "guardian"
    OTHER = "other"


class PlanType(str, enum.Enum):
    """Subscription plan types"""
    BASIC = "basic"
    PREMIUM_MCQ = "premium_mcq"
    PREMIUM = "premium"
    CENTUM = "centum"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"


class QuestionType(str, enum.Enum):
    """Question types"""
    MCQ = "MCQ"  # Multiple Choice Question (1 mark)
    VSA = "VSA"  # Very Short Answer (2 marks)
    SA = "SA"    # Short Answer (3 marks)
    LA = "LA"    # Long Answer (5-6 marks)


class QuestionDifficulty(str, enum.Enum):
    """Question difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionStatus(str, enum.Enum):
    """Question status in question bank"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ExamType(str, enum.Enum):
    """Exam types"""
    BOARD_EXAM = "board_exam"           # Full CBSE board pattern
    SECTION_MCQ = "section_mcq"         # MCQ section only
    SECTION_VSA = "section_vsa"         # VSA section only
    SECTION_SA = "section_sa"           # SA section only
    UNIT_PRACTICE = "unit_practice"     # Unit-specific practice


class ExamStatus(str, enum.Enum):
    """Exam instance status lifecycle"""
    CREATED = "created"                       # Exam generated, not started
    IN_PROGRESS = "in_progress"               # Student is taking the exam
    SUBMITTED_MCQ = "submitted_mcq"           # MCQ answers submitted
    PENDING_UPLOAD = "pending_upload"         # Awaiting answer sheet upload
    UPLOADED = "uploaded"                     # Answer sheets uploaded
    PENDING_EVALUATION = "pending_evaluation" # Assigned to teacher
    EVALUATED = "evaluated"                   # Fully evaluated with final score


class EvaluationStatus(str, enum.Enum):
    """Evaluation workflow status"""
    ASSIGNED = "assigned"         # Assigned to teacher, not started
    IN_PROGRESS = "in_progress"   # Teacher is evaluating
    COMPLETED = "completed"       # Evaluation finished
