"""
Notification Routes

API endpoints for notification management and delivery.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database import get_session
from models import User
from dependencies.auth import (
    get_current_active_user, require_admin, require_student
)
from schemas.notification import (
    CreateNotificationRequest,
    NotificationResponse,
    NotificationListResponse,
    MarkNotificationReadRequest,
    NotificationPreferencesRequest,
    NotificationPreferencesResponse,
    NotificationStatsResponse,
    EvaluationCompleteAlert,
    SLAReminderAlert,
    SLABreachAlert,
    SubscriptionExpiringAlert,
    ExamLimitWarningAlert
)
from services import notification_service


router = APIRouter()


# ==================== User Notifications ====================

@router.get("/notifications", response_model=NotificationListResponse)
async def get_my_notifications(
    page: int = 1,
    page_size: int = 20,
    is_read: Optional[bool] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get my notifications (paginated)

    - Returns all notifications for current user
    - Filter by read status and category
    - Excludes expired notifications

    **Permissions**: All authenticated users
    """
    notifications, total, unread_count = await notification_service.get_user_notifications(
        session,
        str(current_user.user_id),
        page,
        page_size,
        is_read,
        category
    )

    notification_responses = [
        NotificationResponse(
            notification_id=str(n.notification_id),
            user_id=str(n.user_id),
            category=n.category,
            priority=n.priority,
            title=n.title,
            message=n.message,
            notification_types=n.notification_types,
            status=n.status,
            is_read=n.is_read,
            read_at=n.read_at,
            action_url=n.action_url,
            metadata=n.metadata,
            created_at=n.created_at,
            sent_at=n.sent_at,
            expires_at=n.expires_at
        )
        for n in notifications
    ]

    total_pages = (total + page_size - 1) // page_size

    return NotificationListResponse(
        notifications=notification_responses,
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/notifications/mark-read")
async def mark_notifications_read(
    request: MarkNotificationReadRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Mark notifications as read

    - Marks up to 100 notifications as read
    - User can only mark own notifications

    **Permissions**: All authenticated users
    """
    count = await notification_service.mark_notifications_read(
        session,
        request.notification_ids,
        str(current_user.user_id)
    )

    return {
        "success": True,
        "marked_count": count
    }


@router.get("/notifications/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get my notification preferences

    **Permissions**: All authenticated users
    """
    preferences = await notification_service._get_user_preferences(
        session,
        str(current_user.user_id)
    )

    return NotificationPreferencesResponse(
        user_id=str(preferences.user_id),
        email_enabled=preferences.email_enabled,
        sms_enabled=preferences.sms_enabled,
        in_app_enabled=preferences.in_app_enabled,
        push_enabled=preferences.push_enabled,
        evaluation_complete=preferences.evaluation_complete,
        sla_reminders=preferences.sla_reminders,
        subscription_alerts=preferences.subscription_alerts,
        performance_reports=preferences.performance_reports,
        parent_updates=preferences.parent_updates,
        system_announcements=preferences.system_announcements,
        daily_digest=preferences.daily_digest,
        weekly_digest=preferences.weekly_digest,
        updated_at=preferences.updated_at
    )


@router.put("/notifications/preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    request: NotificationPreferencesRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Update my notification preferences

    - Control which channels to receive notifications
    - Control which categories to receive
    - Enable/disable digest emails

    **Permissions**: All authenticated users
    """
    preferences = await notification_service.update_user_preferences(
        session,
        str(current_user.user_id),
        email_enabled=request.email_enabled,
        sms_enabled=request.sms_enabled,
        in_app_enabled=request.in_app_enabled,
        push_enabled=request.push_enabled,
        evaluation_complete=request.evaluation_complete,
        sla_reminders=request.sla_reminders,
        subscription_alerts=request.subscription_alerts,
        performance_reports=request.performance_reports,
        parent_updates=request.parent_updates,
        system_announcements=request.system_announcements,
        daily_digest=request.daily_digest,
        weekly_digest=request.weekly_digest
    )

    return NotificationPreferencesResponse(
        user_id=str(preferences.user_id),
        email_enabled=preferences.email_enabled,
        sms_enabled=preferences.sms_enabled,
        in_app_enabled=preferences.in_app_enabled,
        push_enabled=preferences.push_enabled,
        evaluation_complete=preferences.evaluation_complete,
        sla_reminders=preferences.sla_reminders,
        subscription_alerts=preferences.subscription_alerts,
        performance_reports=preferences.performance_reports,
        parent_updates=preferences.parent_updates,
        system_announcements=preferences.system_announcements,
        daily_digest=preferences.daily_digest,
        weekly_digest=preferences.weekly_digest,
        updated_at=preferences.updated_at
    )


# ==================== Alert Endpoints (Internal/System) ====================

@router.post("/notifications/alert/evaluation-complete", response_model=NotificationResponse)
async def send_evaluation_complete_alert(
    alert: EvaluationCompleteAlert,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Send evaluation complete notification

    - Notifies student when evaluation is done
    - Includes score and percentage
    - Called by evaluation service

    **Permissions**: Admin only (system endpoint)
    """
    try:
        notification = await notification_service.send_evaluation_complete_alert(
            session,
            alert
        )

        return NotificationResponse(
            notification_id=str(notification.notification_id),
            user_id=str(notification.user_id),
            category=notification.category,
            priority=notification.priority,
            title=notification.title,
            message=notification.message,
            notification_types=notification.notification_types,
            status=notification.status,
            is_read=notification.is_read,
            read_at=notification.read_at,
            action_url=notification.action_url,
            metadata=notification.metadata,
            created_at=notification.created_at,
            sent_at=notification.sent_at,
            expires_at=notification.expires_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/notifications/alert/sla-reminder", response_model=NotificationResponse)
async def send_sla_reminder_alert(
    alert: SLAReminderAlert,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Send SLA reminder notification

    - Reminds teacher of upcoming deadline
    - Called by background scheduler

    **Permissions**: Admin only (system endpoint)
    """
    try:
        notification = await notification_service.send_sla_reminder_alert(
            session,
            alert
        )

        return NotificationResponse(
            notification_id=str(notification.notification_id),
            user_id=str(notification.user_id),
            category=notification.category,
            priority=notification.priority,
            title=notification.title,
            message=notification.message,
            notification_types=notification.notification_types,
            status=notification.status,
            is_read=notification.is_read,
            read_at=notification.read_at,
            action_url=notification.action_url,
            metadata=notification.metadata,
            created_at=notification.created_at,
            sent_at=notification.sent_at,
            expires_at=notification.expires_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/notifications/alert/sla-breach", response_model=NotificationResponse)
async def send_sla_breach_alert(
    alert: SLABreachAlert,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Send SLA breach notification

    - Alerts teacher that deadline was missed
    - Called by background scheduler

    **Permissions**: Admin only (system endpoint)
    """
    try:
        notification = await notification_service.send_sla_breach_alert(
            session,
            alert
        )

        return NotificationResponse(
            notification_id=str(notification.notification_id),
            user_id=str(notification.user_id),
            category=notification.category,
            priority=notification.priority,
            title=notification.title,
            message=notification.message,
            notification_types=notification.notification_types,
            status=notification.status,
            is_read=notification.is_read,
            read_at=notification.read_at,
            action_url=notification.action_url,
            metadata=notification.metadata,
            created_at=notification.created_at,
            sent_at=notification.sent_at,
            expires_at=notification.expires_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/notifications/alert/subscription-expiring", response_model=NotificationResponse)
async def send_subscription_expiring_alert(
    alert: SubscriptionExpiringAlert,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Send subscription expiring notification

    - Alerts user that subscription is expiring soon
    - Called by background scheduler

    **Permissions**: Admin only (system endpoint)
    """
    try:
        notification = await notification_service.send_subscription_expiring_alert(
            session,
            alert
        )

        return NotificationResponse(
            notification_id=str(notification.notification_id),
            user_id=str(notification.user_id),
            category=notification.category,
            priority=notification.priority,
            title=notification.title,
            message=notification.message,
            notification_types=notification.notification_types,
            status=notification.status,
            is_read=notification.is_read,
            read_at=notification.read_at,
            action_url=notification.action_url,
            metadata=notification.metadata,
            created_at=notification.created_at,
            sent_at=notification.sent_at,
            expires_at=notification.expires_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/notifications/alert/exam-limit-warning", response_model=NotificationResponse)
async def send_exam_limit_warning_alert(
    alert: ExamLimitWarningAlert,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Send exam limit warning notification

    - Alerts user they're running low on exams
    - Called when usage reaches 80%

    **Permissions**: Admin only (system endpoint)
    """
    try:
        notification = await notification_service.send_exam_limit_warning_alert(
            session,
            alert
        )

        return NotificationResponse(
            notification_id=str(notification.notification_id),
            user_id=str(notification.user_id),
            category=notification.category,
            priority=notification.priority,
            title=notification.title,
            message=notification.message,
            notification_types=notification.notification_types,
            status=notification.status,
            is_read=notification.is_read,
            read_at=notification.read_at,
            action_url=notification.action_url,
            metadata=notification.metadata,
            created_at=notification.created_at,
            sent_at=notification.sent_at,
            expires_at=notification.expires_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== Admin ====================

@router.get("/notifications/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Get notification statistics

    - Total sent/pending/failed
    - By type and category
    - Delivery and read rates

    **Permissions**: Admin only
    """
    stats = await notification_service.get_notification_stats(session)

    return NotificationStatsResponse(
        total_sent=stats['total_sent'],
        total_pending=stats['total_pending'],
        total_failed=stats['total_failed'],
        emails_sent=stats['emails_sent'],
        sms_sent=stats['sms_sent'],
        in_app_sent=stats['in_app_sent'],
        push_sent=stats['push_sent'],
        by_category=stats['by_category'],
        delivery_rate=stats['delivery_rate'],
        read_rate=stats['read_rate']
    )
