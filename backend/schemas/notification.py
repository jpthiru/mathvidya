"""
Notification Schemas

Pydantic models for notifications, emails, and alerts.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    """Notification types"""
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    PUSH = "push"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationCategory(str, Enum):
    """Notification categories"""
    EVALUATION_COMPLETE = "evaluation_complete"
    SLA_REMINDER = "sla_reminder"
    SLA_BREACH = "sla_breach"
    SUBSCRIPTION_EXPIRING = "subscription_expiring"
    SUBSCRIPTION_EXPIRED = "subscription_expired"
    EXAM_LIMIT_WARNING = "exam_limit_warning"
    PERFORMANCE_REPORT = "performance_report"
    TEACHER_ASSIGNMENT = "teacher_assignment"
    PARENT_UPDATE = "parent_update"
    SYSTEM_ANNOUNCEMENT = "system_announcement"


# ==================== Email Templates ====================

class EmailTemplate(BaseModel):
    """Email template structure"""
    template_name: str
    subject: str
    body_html: str
    body_text: Optional[str] = None
    variables: List[str] = Field(default_factory=list, description="Template variables")


class EmailRecipient(BaseModel):
    """Email recipient"""
    email: EmailStr
    name: Optional[str] = None


class SendEmailRequest(BaseModel):
    """Request to send email"""
    to: List[EmailRecipient] = Field(..., min_items=1, description="Recipients")
    subject: str = Field(..., min_length=1, max_length=200)
    body_html: str = Field(..., description="HTML email body")
    body_text: Optional[str] = Field(None, description="Plain text alternative")

    cc: Optional[List[EmailRecipient]] = None
    bcc: Optional[List[EmailRecipient]] = None

    template_name: Optional[str] = Field(None, description="Email template to use")
    template_variables: Optional[Dict[str, Any]] = Field(None, description="Template variable values")

    attachments: Optional[List[str]] = Field(None, description="S3 keys of attachments")

    priority: NotificationPriority = NotificationPriority.MEDIUM
    send_at: Optional[datetime] = Field(None, description="Schedule for future delivery")


class EmailResponse(BaseModel):
    """Email send response"""
    email_id: str
    status: str  # sent, queued, failed
    message_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    error: Optional[str] = None


# ==================== Notifications ====================

class CreateNotificationRequest(BaseModel):
    """Create notification"""
    user_id: str
    category: NotificationCategory
    priority: NotificationPriority = NotificationPriority.MEDIUM

    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)

    notification_types: List[NotificationType] = Field(
        default=[NotificationType.EMAIL, NotificationType.IN_APP],
        description="Delivery channels"
    )

    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    action_url: Optional[str] = Field(None, description="Link for user action")
    expires_at: Optional[datetime] = Field(None, description="Expiration for in-app notifications")


class NotificationResponse(BaseModel):
    """Notification details"""
    notification_id: str
    user_id: str
    category: str
    priority: str

    title: str
    message: str

    notification_types: List[str]

    status: str  # pending, sent, failed, read
    is_read: bool
    read_at: Optional[datetime]

    action_url: Optional[str]
    metadata: Optional[Dict[str, Any]]

    created_at: datetime
    sent_at: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Paginated notifications"""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int
    total_pages: int


class MarkNotificationReadRequest(BaseModel):
    """Mark notification as read"""
    notification_ids: List[str] = Field(..., min_items=1, max_items=100)


class NotificationPreferencesRequest(BaseModel):
    """User notification preferences"""
    email_enabled: bool = True
    sms_enabled: bool = False
    in_app_enabled: bool = True
    push_enabled: bool = False

    # Category preferences
    evaluation_complete: bool = True
    sla_reminders: bool = True
    subscription_alerts: bool = True
    performance_reports: bool = True
    parent_updates: bool = True
    system_announcements: bool = True

    # Digest settings
    daily_digest: bool = False
    weekly_digest: bool = False


class NotificationPreferencesResponse(BaseModel):
    """User notification preferences"""
    user_id: str
    email_enabled: bool
    sms_enabled: bool
    in_app_enabled: bool
    push_enabled: bool

    evaluation_complete: bool
    sla_reminders: bool
    subscription_alerts: bool
    performance_reports: bool
    parent_updates: bool
    system_announcements: bool

    daily_digest: bool
    weekly_digest: bool

    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Alert Templates ====================

class EvaluationCompleteAlert(BaseModel):
    """Evaluation completion notification"""
    student_user_id: str
    student_name: str
    exam_instance_id: str
    exam_type: str
    total_score: float
    percentage: float
    evaluated_at: datetime


class SLAReminderAlert(BaseModel):
    """SLA deadline reminder"""
    teacher_user_id: str
    teacher_name: str
    evaluation_id: str
    exam_instance_id: str
    student_name: str
    sla_deadline: datetime
    hours_remaining: int


class SLABreachAlert(BaseModel):
    """SLA breach notification"""
    evaluation_id: str
    teacher_user_id: str
    teacher_name: str
    exam_instance_id: str
    student_name: str
    sla_deadline: datetime
    hours_overdue: int


class SubscriptionExpiringAlert(BaseModel):
    """Subscription expiring soon"""
    user_id: str
    user_name: str
    subscription_id: str
    plan_name: str
    expiry_date: datetime
    days_remaining: int


class ExamLimitWarningAlert(BaseModel):
    """Exam limit warning"""
    user_id: str
    user_name: str
    exams_used: int
    exams_limit: int
    exams_remaining: int
    reset_date: datetime


class PerformanceReportAlert(BaseModel):
    """Performance report ready"""
    student_user_id: str
    student_name: str
    report_type: str
    report_url: str
    generated_at: datetime


# ==================== Bulk Operations ====================

class BulkNotificationRequest(BaseModel):
    """Send notification to multiple users"""
    user_ids: List[str] = Field(..., min_items=1, max_items=1000)
    category: NotificationCategory
    priority: NotificationPriority = NotificationPriority.MEDIUM

    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)

    notification_types: List[NotificationType] = Field(
        default=[NotificationType.EMAIL, NotificationType.IN_APP]
    )

    action_url: Optional[str] = None


class BulkNotificationResponse(BaseModel):
    """Bulk notification result"""
    total_requested: int
    successful: int
    failed: int
    queued: int
    notification_ids: List[str]
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# ==================== Admin ====================

class NotificationStatsResponse(BaseModel):
    """Notification statistics"""
    total_sent: int
    total_pending: int
    total_failed: int

    # By type
    emails_sent: int
    sms_sent: int
    in_app_sent: int
    push_sent: int

    # By category
    by_category: Dict[str, int]

    # Success rate
    delivery_rate: float
    read_rate: float  # For in-app notifications


class ScheduledNotificationRequest(BaseModel):
    """Schedule recurring notification"""
    category: NotificationCategory
    title: str
    message: str

    schedule_type: str = Field(..., pattern="^(daily|weekly|monthly)$")
    schedule_time: str = Field(..., description="Time in HH:MM format")
    schedule_day: Optional[int] = Field(None, ge=1, le=31, description="Day of month (for monthly)")

    target_users: str = Field(..., pattern="^(all|students|teachers|parents)$")

    is_active: bool = True


class ScheduledNotificationResponse(BaseModel):
    """Scheduled notification details"""
    schedule_id: str
    category: str
    title: str
    message: str

    schedule_type: str
    schedule_time: str
    schedule_day: Optional[int]

    target_users: str
    is_active: bool

    last_sent: Optional[datetime]
    next_scheduled: datetime

    created_at: datetime

    class Config:
        from_attributes = True


class TestNotificationRequest(BaseModel):
    """Test notification delivery"""
    notification_type: NotificationType
    recipient_email: Optional[EmailStr] = None
    recipient_phone: Optional[str] = None
    test_message: str = Field(default="This is a test notification from Mathvidya")
