"""Seed reference data - subscription plans, holidays, system config

Revision ID: 002
Revises: 001
Create Date: 2025-12-23

Seeds initial data for subscription plans, national holidays, and system configuration.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========================================
    # 1. SEED SUBSCRIPTION PLANS
    # ========================================

    op.execute("""
        INSERT INTO subscription_plans (
            plan_type, display_name, description,
            exams_per_month, teacher_hours_per_month,
            allow_board_exam, allow_section_practice, allow_unit_practice, allow_mcq_only,
            leaderboard_eligible, sla_hours,
            monthly_price_paise, annual_price_paise
        ) VALUES
        -- Basic Plan
        (
            'basic', 'Basic Plan',
            'Perfect for beginners - includes 5 full board exams per month with teacher evaluation',
            5, 1.0,
            true, true, false, true,
            false, 48,
            29900, 299900
        ),
        -- Premium MCQ Plan
        (
            'premium_mcq', 'Premium MCQ',
            'MCQ-focused practice - 15 MCQ exams per month with instant results',
            15, 0,
            true, true, false, true,
            false, 48,
            49900, 499900
        ),
        -- Premium Plan
        (
            'premium', 'Premium Plan',
            'Comprehensive preparation - 50 exams per month with full teacher support and leaderboard access',
            50, 1.0,
            true, true, true, true,
            true, 48,
            99900, 999900
        ),
        -- Plan Centum
        (
            'centum', 'Plan Centum',
            'Elite preparation - 50 exams per month with same-day evaluation, direct teacher access, and leaderboard',
            50, NULL,
            true, true, true, true,
            true, 24,
            149900, 1499900
        )
        ON CONFLICT (plan_type) DO NOTHING
    """)

    # ========================================
    # 2. SEED NATIONAL HOLIDAYS (2025-2026)
    # ========================================

    op.execute("""
        INSERT INTO holidays (holiday_date, holiday_name, holiday_type) VALUES
        -- 2025 National Holidays
        ('2025-01-26', 'Republic Day', 'national'),
        ('2025-03-14', 'Holi', 'national'),
        ('2025-04-10', 'Id-ul-Fitr', 'national'),
        ('2025-04-14', 'Ambedkar Jayanti', 'national'),
        ('2025-04-18', 'Good Friday', 'national'),
        ('2025-05-01', 'May Day', 'national'),
        ('2025-08-15', 'Independence Day', 'national'),
        ('2025-08-27', 'Janmashtami', 'national'),
        ('2025-10-02', 'Gandhi Jayanti', 'national'),
        ('2025-10-02', 'Dussehra', 'national'),
        ('2025-10-21', 'Diwali', 'national'),
        ('2025-11-05', 'Guru Nanak Jayanti', 'national'),
        ('2025-12-25', 'Christmas', 'national'),

        -- 2026 National Holidays (for planning)
        ('2026-01-26', 'Republic Day', 'national'),
        ('2026-03-06', 'Holi', 'national'),
        ('2026-03-31', 'Id-ul-Fitr', 'national'),
        ('2026-04-03', 'Good Friday', 'national'),
        ('2026-04-14', 'Ambedkar Jayanti', 'national'),
        ('2026-05-01', 'May Day', 'national'),
        ('2026-08-15', 'Independence Day', 'national'),
        ('2026-08-16', 'Janmashtami', 'national'),
        ('2026-10-02', 'Gandhi Jayanti', 'national'),
        ('2026-10-12', 'Dussehra', 'national'),
        ('2026-11-01', 'Diwali', 'national'),
        ('2026-11-25', 'Guru Nanak Jayanti', 'national'),
        ('2026-12-25', 'Christmas', 'national')
        ON CONFLICT (holiday_date) DO NOTHING
    """)

    # ========================================
    # 3. SEED SYSTEM CONFIGURATION
    # ========================================

    op.execute("""
        INSERT INTO system_config (config_key, config_value, description) VALUES
        -- SLA Working Hours
        (
            'sla_working_hours',
            '{"start": "09:00", "end": "18:00", "timezone": "Asia/Kolkata"}'::jsonb,
            'Working hours for SLA calculations (Indian Standard Time)'
        ),
        -- Leaderboard Configuration
        (
            'leaderboard_top_n',
            '10'::jsonb,
            'Number of students shown on public leaderboard'
        ),
        -- Upload Limits
        (
            'max_upload_size_mb',
            '5'::jsonb,
            'Maximum answer sheet upload size in megabytes'
        ),
        (
            'allowed_upload_mimetypes',
            '["image/jpeg", "image/jpg", "image/png", "application/pdf"]'::jsonb,
            'Allowed MIME types for answer sheet uploads'
        ),
        -- Teacher Evaluation UI
        (
            'evaluation_ui_stamps',
            '["tick", "cross", "half", "circle", "star"]'::jsonb,
            'Available annotation stamps for teachers during evaluation'
        ),
        -- Analytics Configuration
        (
            'analytics_refresh_hour',
            '2'::jsonb,
            'Hour of day (IST) to refresh analytics materialized views (0-23)'
        ),
        (
            'analytics_retention_days',
            '730'::jsonb,
            'Number of days to retain detailed analytics data (2 years)'
        ),
        -- Exam Configuration
        (
            'exam_auto_submit_enabled',
            'true'::jsonb,
            'Automatically submit exam when duration expires'
        ),
        (
            'exam_grace_period_minutes',
            '5'::jsonb,
            'Grace period after exam duration before auto-submission'
        ),
        -- Notification Configuration
        (
            'notifications_enabled',
            'true'::jsonb,
            'Global toggle for email/SMS notifications'
        ),
        (
            'notification_email_from',
            '"Mathvidya <noreply@mathvidya.com>"'::jsonb,
            'From address for email notifications'
        ),
        -- Question Bank Configuration
        (
            'question_approval_required',
            'true'::jsonb,
            'Require admin approval for teacher-created questions'
        ),
        -- Security Configuration
        (
            'session_timeout_minutes',
            '60'::jsonb,
            'User session timeout in minutes'
        ),
        (
            'max_login_attempts',
            '5'::jsonb,
            'Maximum failed login attempts before account lock'
        ),
        -- S3 Configuration (placeholder - actual values in environment)
        (
            'aws_s3_region',
            '"ap-south-1"'::jsonb,
            'AWS S3 region for file storage (Mumbai)'
        ),
        (
            's3_signed_url_expiry_minutes',
            '15'::jsonb,
            'Signed URL expiry time for S3 downloads (minutes)'
        ),
        -- CBSE Unit Names for Class XII
        (
            'cbse_units_class_xii',
            '[
                "Relations and Functions",
                "Inverse Trigonometric Functions",
                "Matrices",
                "Determinants",
                "Continuity and Differentiability",
                "Application of Derivatives",
                "Integrals",
                "Application of Integrals",
                "Differential Equations",
                "Vector Algebra",
                "Three Dimensional Geometry",
                "Linear Programming",
                "Probability"
            ]'::jsonb,
            'CBSE unit names for Class XII Mathematics'
        ),
        -- CBSE Unit Names for Class X
        (
            'cbse_units_class_x',
            '[
                "Real Numbers",
                "Polynomials",
                "Pair of Linear Equations in Two Variables",
                "Quadratic Equations",
                "Arithmetic Progressions",
                "Triangles",
                "Coordinate Geometry",
                "Introduction to Trigonometry",
                "Some Applications of Trigonometry",
                "Circles",
                "Areas Related to Circles",
                "Surface Areas and Volumes",
                "Statistics",
                "Probability"
            ]'::jsonb,
            'CBSE unit names for Class X Mathematics'
        )
        ON CONFLICT (config_key) DO NOTHING
    """)


def downgrade() -> None:
    # Delete all seeded data
    op.execute("DELETE FROM system_config WHERE config_key IN ('sla_working_hours', 'leaderboard_top_n', 'max_upload_size_mb', 'allowed_upload_mimetypes', 'evaluation_ui_stamps', 'analytics_refresh_hour', 'analytics_retention_days', 'exam_auto_submit_enabled', 'exam_grace_period_minutes', 'notifications_enabled', 'notification_email_from', 'question_approval_required', 'session_timeout_minutes', 'max_login_attempts', 'aws_s3_region', 's3_signed_url_expiry_minutes', 'cbse_units_class_xii', 'cbse_units_class_x')")
    op.execute("DELETE FROM holidays WHERE holiday_date BETWEEN '2025-01-01' AND '2026-12-31'")
    op.execute("DELETE FROM subscription_plans WHERE plan_type IN ('basic', 'premium_mcq', 'premium', 'centum')")
