"""
Email Service

Handles sending emails via AWS SES SMTP.
Provides reusable email functionality for verification, notifications, etc.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

from config.settings import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via AWS SES"""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAILS_FROM_EMAIL
        self.from_name = settings.EMAILS_FROM_NAME

    def _get_smtp_connection(self):
        """Create SMTP connection with TLS"""
        context = ssl.create_default_context()
        server = smtplib.SMTP(self.smtp_host, self.smtp_port)
        server.starttls(context=context)
        server.login(self.smtp_user, self.smtp_password)
        return server

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body of the email
            text_content: Plain text alternative (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email

            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)

            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

            # Send email
            with self._get_smtp_connection() as server:
                server.sendmail(self.from_email, to_email, message.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email to {to_email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {e}")
            return False

    def send_verification_email(self, to_email: str, code: str, first_name: str) -> bool:
        """
        Send email verification code

        Args:
            to_email: User's email address
            code: 6-digit verification code
            first_name: User's first name for personalization

        Returns:
            True if sent successfully
        """
        subject = f"Verify your Mathvidya account - {code}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">Mathvidya</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0;">Your CBSE Mathematics Practice Platform</p>
            </div>

            <div style="background: #ffffff; padding: 40px 30px; border: 1px solid #e0e0e0; border-top: none;">
                <h2 style="color: #333; margin-top: 0;">Hi {first_name},</h2>

                <p>Welcome to Mathvidya! Please use the verification code below to complete your registration:</p>

                <div style="background: #f8f9fa; border: 2px dashed #667eea; border-radius: 10px; padding: 30px; text-align: center; margin: 30px 0;">
                    <p style="margin: 0 0 10px 0; color: #666; font-size: 14px;">Your verification code is:</p>
                    <div style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #667eea;">{code}</div>
                </div>

                <p style="color: #666; font-size: 14px;">This code will expire in <strong>15 minutes</strong>.</p>

                <p style="color: #666; font-size: 14px;">If you didn't create an account on Mathvidya, please ignore this email.</p>
            </div>

            <div style="background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; border: 1px solid #e0e0e0; border-top: none;">
                <p style="margin: 0; color: #999; font-size: 12px;">
                    This is an automated message from Mathvidya.<br>
                    Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Hi {first_name},

        Welcome to Mathvidya! Please use the verification code below to complete your registration:

        Your verification code: {code}

        This code will expire in 15 minutes.

        If you didn't create an account on Mathvidya, please ignore this email.

        - The Mathvidya Team
        """

        return self.send_email(to_email, subject, html_content, text_content)

    def send_password_reset_email(self, to_email: str, code: str, first_name: str) -> bool:
        """
        Send password reset code

        Args:
            to_email: User's email address
            code: 6-digit reset code
            first_name: User's first name

        Returns:
            True if sent successfully
        """
        subject = f"Reset your Mathvidya password - {code}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">Mathvidya</h1>
            </div>

            <div style="background: #ffffff; padding: 40px 30px; border: 1px solid #e0e0e0; border-top: none;">
                <h2 style="color: #333; margin-top: 0;">Hi {first_name},</h2>

                <p>We received a request to reset your password. Use the code below to proceed:</p>

                <div style="background: #fff3cd; border: 2px dashed #ffc107; border-radius: 10px; padding: 30px; text-align: center; margin: 30px 0;">
                    <p style="margin: 0 0 10px 0; color: #666; font-size: 14px;">Your password reset code is:</p>
                    <div style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #856404;">{code}</div>
                </div>

                <p style="color: #666; font-size: 14px;">This code will expire in <strong>15 minutes</strong>.</p>

                <p style="color: #dc3545; font-size: 14px;"><strong>If you didn't request a password reset, please ignore this email and your password will remain unchanged.</strong></p>
            </div>

            <div style="background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; border: 1px solid #e0e0e0; border-top: none;">
                <p style="margin: 0; color: #999; font-size: 12px;">
                    This is an automated message from Mathvidya.<br>
                    Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Hi {first_name},

        We received a request to reset your password. Use the code below to proceed:

        Your password reset code: {code}

        This code will expire in 15 minutes.

        If you didn't request a password reset, please ignore this email and your password will remain unchanged.

        - The Mathvidya Team
        """

        return self.send_email(to_email, subject, html_content, text_content)


# Global email service instance
email_service = EmailService()
