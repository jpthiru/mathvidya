"""Dependency injection modules for FastAPI"""

from .auth import (
    get_current_user,
    get_current_active_user,
    require_role,
    require_student,
    require_teacher,
    require_admin,
    require_parent,
    require_student_or_parent,
    require_teacher_or_admin,
    create_access_token
)

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "require_role",
    "require_student",
    "require_teacher",
    "require_admin",
    "require_parent",
    "require_student_or_parent",
    "require_teacher_or_admin",
    "create_access_token",
]
