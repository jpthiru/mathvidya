"""
Notification Service

Business logic for notifications, emails, and alerts.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import uuid4
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from models import (
    User, Notification, NotificationPreference
)
from schemas.notification import (
    NotificationType, NotificationCategory, NotificationPriority,
    CreateNotificationRequest, SendEmailRequest,
    EvaluationCompleteAlert, SLAReminderAlert, SLABreachAlert,
    SubscriptionExpiringAlert, ExamLimitWarningAlert
)


class NotificationService:
    """Service for notification management"""

    # Email configuration (should be loaded from environment variables in production)
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = "noreply@mathvidya.com"
    SMTP_PASSWORD = "your-app-password"  # Use environment variable
    FROM_EMAIL = "Mathvidya <noreply@mathvidya.com>"

    @staticmethod
    async def create_notification(
        session: AsyncSession,
        request: CreateNotificationRequest
    ) -> Notification:
        """
        Create a new notification

        Args:
            session: Database session
            request: Notification creation request

        Returns:
            Created notification
        """
        # Check user preferences
        preferences = await NotificationService._get_user_preferences(
            session,
            request.user_id
        )

        # Filter notification types based on preferences
        allowed_types = NotificationService._filter_by_preferences(
            request.notification_types,
            request.category,
            preferences
        )

        if not allowed_types:
            raise ValueError(f"User has disabled all notification channels for {request.category}")

        # Create notification record
        notification = Notification(
            notification_id=uuid4(),
            user_id=request.user_id,
            category=request.category.value,
            priority=request.priority.value,
            title=request.title,
            message=request.message,
            notification_types=[nt.value for nt in allowed_types],
            status='pending',
            is_read=False,
            action_url=request.action_url,
            extra_data=request.metadata,
            expires_at=request.expires_at,
            created_at=datetime.utcnow()
        )

        session.add(notification)
        await session.commit()
        await session.refresh(notification)

        return notification

    @staticmethod
    async def send_notification(
        session: AsyncSession,
        notification: Notification
    ) -> bool:
        """
        Send notification via all configured channels

        Args:
            session: Database session
            notification: Notification to send

        Returns:
            True if sent successfully
        """
        success = True

        try:
            # Get user details
            user = await session.get(User, notification.user_id)
            if not user:
                raise ValueError(f"User not found: {notification.user_id}")

            # Send via each channel
            if NotificationType.EMAIL.value in notification.notification_types:
                email_success = await NotificationService._send_email_notification(
                    user.email,
                    user.full_name,
                    notification.title,
                    notification.message,
                    notification.action_url
                )
                success = success and email_success

            if NotificationType.SMS.value in notification.notification_types:
                # SMS integration placeholder
                pass

            if NotificationType.IN_APP.value in notification.notification_types:
                # In-app notification is already stored in database
                pass

            if NotificationType.PUSH.value in notification.notification_types:
                # Push notification integration placeholder
                pass

            # Update notification status
            notification.status = 'sent' if success else 'failed'
            notification.sent_at = datetime.utcnow()
            await session.commit()

            return success

        except Exception as e:
            notification.status = 'failed'
            notification.extra_data = notification.extra_data or {}
            notification.extra_data['error'] = str(e)
            await session.commit()
            return False

    @staticmethod
    async def _send_email_notification(
        to_email: str,
        to_name: str,
        subject: str,
        message: str,
        action_url: Optional[str] = None
    ) -> bool:
        """
        Send email notification

        Args:
            to_email: Recipient email
            to_name: Recipient name
            subject: Email subject
            message: Email message
            action_url: Optional action URL

        Returns:
            True if sent successfully
        """
        try:
            # Create email
            msg = MIMEMultipart('alternative')
            msg['From'] = NotificationService.FROM_EMAIL
            msg['To'] = f"{to_name} <{to_email}>"
            msg['Subject'] = subject

            # Create HTML body
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; }}
                    .button {{ display: inline-block; padding: 10px 20px; background-color: #4CAF50;
                              color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                    .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Mathvidya</h1>
                    </div>
                    <div class="content">
                        <h2>{subject}</h2>
                        <p>{message}</p>
                        {f'<a href="{action_url}" class="button">View Details</a>' if action_url else ''}
                    </div>
                    <div class="footer">
                        <p>© 2025 Mathvidya. All rights reserved.</p>
                        <p>This is an automated email. Please do not reply.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Create plain text alternative
            text_body = f"{subject}\n\n{message}"
            if action_url:
                text_body += f"\n\nView details: {action_url}"

            # Attach parts
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)

            # Send email (in production, use proper email service)
            # For now, just log and return success
            print(f"[EMAIL] To: {to_email}, Subject: {subject}")
            print(f"[EMAIL] Message: {message}")

            # Uncomment to actually send emails:
            # with smtplib.SMTP(NotificationService.SMTP_HOST, NotificationService.SMTP_PORT) as server:
            #     server.starttls()
            #     server.login(NotificationService.SMTP_USER, NotificationService.SMTP_PASSWORD)
            #     server.send_message(msg)

            return True

        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send email to {to_email}: {e}")
            return False

    @staticmethod
    async def send_evaluation_complete_alert(
        session: AsyncSession,
        alert: EvaluationCompleteAlert
    ) -> Notification:
        """Send evaluation completion notification"""
        request = CreateNotificationRequest(
            user_id=alert.student_user_id,
            category=NotificationCategory.EVALUATION_COMPLETE,
            priority=NotificationPriority.HIGH,
            title="Your Exam Has Been Evaluated!",
            message=f"Your {alert.exam_type} exam has been evaluated. "
                   f"You scored {alert.total_score} marks ({alert.percentage:.1f}%). "
                   f"Check your dashboard for detailed results.",
            notification_types=[NotificationType.EMAIL, NotificationType.IN_APP],
            metadata={
                'exam_instance_id': alert.exam_instance_id,
                'total_score': alert.total_score,
                'percentage': alert.percentage
            },
            action_url=f"/student/exams/{alert.exam_instance_id}/results"
        )

        notification = await NotificationService.create_notification(session, request)
        await NotificationService.send_notification(session, notification)
        return notification

    @staticmethod
    async def send_sla_reminder_alert(
        session: AsyncSession,
        alert: SLAReminderAlert
    ) -> Notification:
        """Send SLA deadline reminder to teacher"""
        request = CreateNotificationRequest(
            user_id=alert.teacher_user_id,
            category=NotificationCategory.SLA_REMINDER,
            priority=NotificationPriority.URGENT,
            title=f"Evaluation Due in {alert.hours_remaining} Hours",
            message=f"Reminder: Evaluation for {alert.student_name}'s exam is due in "
                   f"{alert.hours_remaining} hours (deadline: {alert.sla_deadline.strftime('%Y-%m-%d %H:%M')}).",
            notification_types=[NotificationType.EMAIL, NotificationType.IN_APP],
            metadata={
                'evaluation_id': alert.evaluation_id,
                'exam_instance_id': alert.exam_instance_id,
                'sla_deadline': alert.sla_deadline.isoformat(),
                'hours_remaining': alert.hours_remaining
            },
            action_url=f"/teacher/evaluations/{alert.evaluation_id}"
        )

        notification = await NotificationService.create_notification(session, request)
        await NotificationService.send_notification(session, notification)
        return notification

    @staticmethod
    async def send_sla_breach_alert(
        session: AsyncSession,
        alert: SLABreachAlert
    ) -> Notification:
        """Send SLA breach notification"""
        request = CreateNotificationRequest(
            user_id=alert.teacher_user_id,
            category=NotificationCategory.SLA_BREACH,
            priority=NotificationPriority.URGENT,
            title="SLA Deadline Missed",
            message=f"URGENT: Evaluation for {alert.student_name}'s exam is overdue by "
                   f"{alert.hours_overdue} hours. Please complete immediately.",
            notification_types=[NotificationType.EMAIL, NotificationType.IN_APP],
            metadata={
                'evaluation_id': alert.evaluation_id,
                'exam_instance_id': alert.exam_instance_id,
                'hours_overdue': alert.hours_overdue
            },
            action_url=f"/teacher/evaluations/{alert.evaluation_id}"
        )

        notification = await NotificationService.create_notification(session, request)
        await NotificationService.send_notification(session, notification)
        return notification

    @staticmethod
    async def send_subscription_expiring_alert(
        session: AsyncSession,
        alert: SubscriptionExpiringAlert
    ) -> Notification:
        """Send subscription expiring notification"""
        request = CreateNotificationRequest(
            user_id=alert.user_id,
            category=NotificationCategory.SUBSCRIPTION_EXPIRING,
            priority=NotificationPriority.HIGH,
            title=f"Your {alert.plan_name} Subscription Expires Soon",
            message=f"Your subscription will expire in {alert.days_remaining} days "
                   f"(on {alert.expiry_date.strftime('%Y-%m-%d')}). Renew now to continue accessing premium features.",
            notification_types=[NotificationType.EMAIL, NotificationType.IN_APP],
            metadata={
                'subscription_id': alert.subscription_id,
                'plan_name': alert.plan_name,
                'days_remaining': alert.days_remaining
            },
            action_url="/student/subscription"
        )

        notification = await NotificationService.create_notification(session, request)
        await NotificationService.send_notification(session, notification)
        return notification

    @staticmethod
    async def send_exam_limit_warning_alert(
        session: AsyncSession,
        alert: ExamLimitWarningAlert
    ) -> Notification:
        """Send exam limit warning"""
        request = CreateNotificationRequest(
            user_id=alert.user_id,
            category=NotificationCategory.EXAM_LIMIT_WARNING,
            priority=NotificationPriority.MEDIUM,
            title=f"Only {alert.exams_remaining} Exams Remaining",
            message=f"You have used {alert.exams_used} of {alert.exams_limit} exams this month. "
                   f"{alert.exams_remaining} exams remaining. Resets on {alert.reset_date.strftime('%Y-%m-%d')}.",
            notification_types=[NotificationType.IN_APP],
            metadata={
                'exams_used': alert.exams_used,
                'exams_limit': alert.exams_limit,
                'exams_remaining': alert.exams_remaining
            },
            action_url="/student/subscription"
        )

        notification = await NotificationService.create_notification(session, request)
        await NotificationService.send_notification(session, notification)
        return notification

    @staticmethod
    async def get_user_notifications(
        session: AsyncSession,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        is_read: Optional[bool] = None,
        category: Optional[str] = None
    ) -> Tuple[List[Notification], int, int]:
        """
        Get user's notifications (paginated)

        Returns:
            Tuple of (notifications, total_count, unread_count)
        """
        # Build query
        query = select(Notification).where(Notification.user_id == user_id)

        # Filter by read status
        if is_read is not None:
            query = query.where(Notification.is_read == is_read)

        # Filter by category
        if category:
            query = query.where(Notification.category == category)

        # Filter out expired notifications
        query = query.where(
            or_(
                Notification.expires_at == None,
                Notification.expires_at > datetime.utcnow()
            )
        )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total_count = total_result.scalar()

        # Get unread count
        unread_query = select(func.count()).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        unread_result = await session.execute(unread_query)
        unread_count = unread_result.scalar()

        # Paginate
        query = query.order_by(Notification.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await session.execute(query)
        notifications = result.scalars().all()

        return list(notifications), total_count, unread_count

    @staticmethod
    async def mark_notifications_read(
        session: AsyncSession,
        notification_ids: List[str],
        user_id: str
    ) -> int:
        """
        Mark notifications as read

        Returns:
            Number of notifications marked as read
        """
        count = 0
        for notification_id in notification_ids:
            notification = await session.get(Notification, notification_id)
            if notification and str(notification.user_id) == user_id:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                count += 1

        await session.commit()
        return count

    @staticmethod
    async def _get_user_preferences(
        session: AsyncSession,
        user_id: str
    ) -> NotificationPreference:
        """Get user's notification preferences (or create defaults)"""
        query = select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
        result = await session.execute(query)
        preferences = result.scalar_one_or_none()

        if not preferences:
            # Create default preferences
            preferences = NotificationPreference(
                preference_id=uuid4(),
                user_id=user_id,
                email_enabled=True,
                sms_enabled=False,
                in_app_enabled=True,
                push_enabled=False,
                evaluation_complete=True,
                sla_reminders=True,
                subscription_alerts=True,
                performance_reports=True,
                parent_updates=True,
                system_announcements=True,
                daily_digest=False,
                weekly_digest=False,
                updated_at=datetime.utcnow()
            )
            session.add(preferences)
            await session.commit()

        return preferences

    @staticmethod
    def _filter_by_preferences(
        notification_types: List[NotificationType],
        category: NotificationCategory,
        preferences: NotificationPreference
    ) -> List[NotificationType]:
        """Filter notification types based on user preferences"""
        allowed = []

        # Check if category is enabled
        category_enabled = True
        if category == NotificationCategory.EVALUATION_COMPLETE:
            category_enabled = preferences.evaluation_complete
        elif category in [NotificationCategory.SLA_REMINDER, NotificationCategory.SLA_BREACH]:
            category_enabled = preferences.sla_reminders
        elif category in [NotificationCategory.SUBSCRIPTION_EXPIRING, NotificationCategory.SUBSCRIPTION_EXPIRED]:
            category_enabled = preferences.subscription_alerts
        elif category == NotificationCategory.PERFORMANCE_REPORT:
            category_enabled = preferences.performance_reports
        elif category == NotificationCategory.PARENT_UPDATE:
            category_enabled = preferences.parent_updates
        elif category == NotificationCategory.SYSTEM_ANNOUNCEMENT:
            category_enabled = preferences.system_announcements

        if not category_enabled:
            return []

        # Filter by channel preferences
        for nt in notification_types:
            if nt == NotificationType.EMAIL and preferences.email_enabled:
                allowed.append(nt)
            elif nt == NotificationType.SMS and preferences.sms_enabled:
                allowed.append(nt)
            elif nt == NotificationType.IN_APP and preferences.in_app_enabled:
                allowed.append(nt)
            elif nt == NotificationType.PUSH and preferences.push_enabled:
                allowed.append(nt)

        return allowed

    @staticmethod
    async def update_user_preferences(
        session: AsyncSession,
        user_id: str,
        **updates
    ) -> NotificationPreference:
        """Update user's notification preferences"""
        preferences = await NotificationService._get_user_preferences(session, user_id)

        # Update fields
        for key, value in updates.items():
            if hasattr(preferences, key):
                setattr(preferences, key, value)

        preferences.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(preferences)

        return preferences

    @staticmethod
    async def get_notification_stats(
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Get notification statistics (admin only)"""
        # Total notifications
        total_query = select(func.count()).select_from(Notification)
        total_result = await session.execute(total_query)
        total_sent = total_result.scalar()

        # By status
        pending_query = select(func.count()).where(Notification.status == 'pending')
        pending_result = await session.execute(pending_query)
        total_pending = pending_result.scalar()

        failed_query = select(func.count()).where(Notification.status == 'failed')
        failed_result = await session.execute(failed_query)
        total_failed = failed_result.scalar()

        # By type (simplified - would need array operations for accurate count)
        sent_query = select(func.count()).where(Notification.status == 'sent')
        sent_result = await session.execute(sent_query)

        # By category
        category_query = select(
            Notification.category,
            func.count(Notification.notification_id)
        ).group_by(Notification.category)
        category_result = await session.execute(category_query)
        by_category = {row[0]: row[1] for row in category_result}

        # Calculate rates
        delivery_rate = (total_sent - total_failed) / total_sent if total_sent > 0 else 0

        read_query = select(func.count()).where(Notification.is_read == True)
        read_result = await session.execute(read_query)
        total_read = read_result.scalar()
        read_rate = total_read / total_sent if total_sent > 0 else 0

        return {
            'total_sent': total_sent,
            'total_pending': total_pending,
            'total_failed': total_failed,
            'emails_sent': 0,  # Would need proper counting
            'sms_sent': 0,
            'in_app_sent': 0,
            'push_sent': 0,
            'by_category': by_category,
            'delivery_rate': delivery_rate,
            'read_rate': read_rate
        }


# Singleton instance
notification_service = NotificationService()
