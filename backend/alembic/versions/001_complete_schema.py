"""Complete database schema - all tables

Revision ID: 001
Revises:
Create Date: 2025-12-23

Creates all 15 tables with relationships, constraints, and indexes.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========================================
    # 1. CREATE ALL ENUM TYPES
    # ========================================

    # User and Relationship Enums
    op.execute("""
        CREATE TYPE mv_user_role AS ENUM ('student', 'parent', 'teacher', 'admin')
    """)

    op.execute("""
        CREATE TYPE mv_relationship_type AS ENUM ('father', 'mother', 'guardian', 'other')
    """)

    # Subscription Enums
    op.execute("""
        CREATE TYPE mv_plan_type AS ENUM ('basic', 'premium_mcq', 'premium', 'centum')
    """)

    op.execute("""
        CREATE TYPE mv_subscription_status AS ENUM ('active', 'expired', 'cancelled', 'pending')
    """)

    # Question Enums
    op.execute("""
        CREATE TYPE mv_question_type AS ENUM ('MCQ', 'VSA', 'SA', 'LA')
    """)

    op.execute("""
        CREATE TYPE mv_question_difficulty AS ENUM ('easy', 'medium', 'hard')
    """)

    op.execute("""
        CREATE TYPE mv_question_status AS ENUM ('draft', 'active', 'archived')
    """)

    # Exam Enums
    op.execute("""
        CREATE TYPE mv_exam_type AS ENUM ('board_exam', 'section_mcq', 'section_vsa', 'section_sa', 'unit_practice')
    """)

    op.execute("""
        CREATE TYPE mv_exam_status AS ENUM ('created', 'in_progress', 'submitted_mcq', 'pending_upload', 'uploaded', 'pending_evaluation', 'evaluated')
    """)

    # Evaluation Enum
    op.execute("""
        CREATE TYPE mv_evaluation_status AS ENUM ('assigned', 'in_progress', 'completed')
    """)

    # ========================================
    # 2. CREATE TABLES IN DEPENDENCY ORDER
    # ========================================

    # ------------------------------
    # 2.1 Users Table (no dependencies)
    # ------------------------------
    op.create_table(
        'users',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', postgresql.ENUM('student', 'parent', 'teacher', 'admin', create_type=False, name='mv_user_role'), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(20)),
        sa.Column('student_class', sa.String(10)),
        sa.Column('student_photo_url', sa.Text()),
        sa.Column('school_name', sa.String(255)),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        sa.CheckConstraint("(role != 'student') OR (student_class IS NOT NULL)", name='mv_student_class_required'),
    )

    # Create indexes for users
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_role', 'users', ['role'])
    op.create_index('idx_users_active', 'users', ['is_active'], postgresql_where=sa.text('is_active = true'))
    op.create_index('idx_users_class', 'users', ['student_class'], postgresql_where=sa.text('student_class IS NOT NULL'))

    # ------------------------------
    # 2.2 Parent-Student Mappings (depends on users)
    # ------------------------------
    op.create_table(
        'parent_student_mappings',
        sa.Column('mapping_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('parent_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship', postgresql.ENUM('father', 'mother', 'guardian', 'other', create_type=False, name='mv_relationship_type'), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('parent_user_id', 'student_user_id', create_type=False, name='mv_unique_parent_student'),
        sa.CheckConstraint('parent_user_id != student_user_id', create_type=False, name='mv_no_self_mapping'),
    )

    op.create_index('idx_parent_mappings_parent', 'parent_student_mappings', ['parent_user_id'])
    op.create_index('idx_parent_mappings_student', 'parent_student_mappings', ['student_user_id'])
    op.create_index('idx_parent_mappings_primary', 'parent_student_mappings', ['student_user_id', 'is_primary'],
                    postgresql_where=sa.text('is_primary = true'))

    # ------------------------------
    # 2.3 Subscription Plans (no dependencies)
    # ------------------------------
    op.create_table(
        'subscription_plans',
        sa.Column('plan_type', postgresql.ENUM('basic', 'premium_mcq', 'premium', 'centum', create_type=False, name='mv_plan_type'), primary_key=True),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('exams_per_month', sa.Integer(), nullable=False),
        sa.Column('teacher_hours_per_month', sa.Numeric(5, 2)),
        sa.Column('allow_board_exam', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('allow_section_practice', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('allow_unit_practice', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('allow_mcq_only', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('leaderboard_eligible', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('sla_hours', sa.Integer(), nullable=False),
        sa.Column('monthly_price_paise', sa.Integer()),
        sa.Column('annual_price_paise', sa.Integer()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint('exams_per_month > 0', create_type=False, name='mv_valid_exams_per_month'),
        sa.CheckConstraint('teacher_hours_per_month IS NULL OR teacher_hours_per_month >= 0', create_type=False, name='mv_valid_teacher_hours'),
        sa.CheckConstraint('sla_hours IN (24, 48)', create_type=False, name='mv_valid_sla_hours'),
        sa.CheckConstraint('monthly_price_paise IS NULL OR monthly_price_paise > 0', create_type=False, name='mv_valid_monthly_price'),
        sa.CheckConstraint('annual_price_paise IS NULL OR annual_price_paise > 0', create_type=False, name='mv_valid_annual_price'),
    )

    op.create_index('idx_subscription_plans_active', 'subscription_plans', ['is_active'],
                    postgresql_where=sa.text('is_active = true'))

    # ------------------------------
    # 2.4 Subscriptions (depends on users, subscription_plans)
    # ------------------------------
    op.create_table(
        'subscriptions',
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('student_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('plan_type', postgresql.ENUM('basic', 'premium_mcq', 'premium', 'centum', create_type=False, name='mv_plan_type'),
                  sa.ForeignKey('subscription_plans.plan_type'), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('billing_cycle', sa.String(20), nullable=False),
        sa.Column('status', postgresql.ENUM('active', 'expired', 'cancelled', 'pending', create_type=False, name='mv_subscription_status'),
                  nullable=False, server_default=sa.text("'active'")),
        sa.Column('exams_used_this_month', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('exams_limit_per_month', sa.Integer(), nullable=False),
        sa.Column('teacher_hours_used', sa.Numeric(5, 2), server_default=sa.text('0')),
        sa.Column('teacher_hours_limit', sa.Numeric(5, 2)),
        sa.Column('billing_day_of_month', sa.Integer(), nullable=False),
        sa.Column('last_counter_reset_date', sa.Date()),
        sa.Column('amount_paid_paise', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default=sa.text("'INR'")),
        sa.Column('payment_gateway', sa.String(50)),
        sa.Column('payment_gateway_ref', sa.String(255)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint('end_date > start_date', create_type=False, name='mv_valid_subscription_dates'),
        sa.CheckConstraint('exams_used_this_month >= 0', create_type=False, name='mv_valid_exams_used'),
        sa.CheckConstraint('teacher_hours_used IS NULL OR teacher_hours_used >= 0', create_type=False, name='mv_valid_hours_used'),
        sa.CheckConstraint("billing_cycle IN ('monthly', 'annual')", create_type=False, name='mv_valid_billing_cycle'),
        sa.CheckConstraint('billing_day_of_month BETWEEN 1 AND 28', create_type=False, name='mv_valid_billing_day'),
    )

    op.create_index('idx_subscriptions_student', 'subscriptions', ['student_user_id'])
    op.create_index('idx_subscriptions_status', 'subscriptions', ['status'])
    op.create_index('idx_subscriptions_active_student', 'subscriptions', ['student_user_id', 'status'],
                    postgresql_where=sa.text("status = 'active'"))
    op.create_index('idx_subscriptions_end_date', 'subscriptions', ['end_date'],
                    postgresql_where=sa.text("status = 'active'"))

    # Exclusion constraint for overlapping active subscriptions (requires btree_gist extension)
    op.execute('CREATE EXTENSION IF NOT EXISTS btree_gist')
    op.execute("""
        ALTER TABLE subscriptions
        ADD CONSTRAINT one_active_per_student
        EXCLUDE USING GIST (
            student_user_id WITH =,
            daterange(start_date, end_date, '[]') WITH &&
        ) WHERE (status = 'active')
    """)

    # ------------------------------
    # 2.5 Questions (depends on users)
    # ------------------------------
    op.create_table(
        'questions',
        sa.Column('question_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('class', sa.String(10), nullable=False),
        sa.Column('unit', sa.String(100), nullable=False),
        sa.Column('topic', sa.String(255)),
        sa.Column('question_type', postgresql.ENUM('MCQ', 'VSA', 'SA', 'LA', create_type=False, name='mv_question_type'), nullable=False),
        sa.Column('marks', sa.Integer(), nullable=False),
        sa.Column('difficulty', postgresql.ENUM('easy', 'medium', 'hard', create_type=False, name='mv_question_difficulty')),
        sa.Column('question_text', sa.Text()),
        sa.Column('question_image_url', sa.Text()),
        sa.Column('diagram_image_url', sa.Text()),
        sa.Column('mcq_choices', postgresql.JSONB()),
        sa.Column('mcq_correct_choices', postgresql.JSONB()),
        sa.Column('correct_answer_text', sa.Text()),
        sa.Column('correct_answer_image_url', sa.Text()),
        sa.Column('explanation', sa.Text()),
        sa.Column('explanation_image_url', sa.Text()),
        sa.Column('cbse_year', sa.Integer()),
        sa.Column('tags', postgresql.ARRAY(sa.String())),
        sa.Column('status', postgresql.ENUM('draft', 'active', 'archived', create_type=False, name='mv_question_status'),
                  nullable=False, server_default=sa.text("'draft'")),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint('question_text IS NOT NULL OR question_image_url IS NOT NULL', create_type=False, name='mv_question_content_required'),
        sa.CheckConstraint("question_type != 'MCQ' OR (mcq_choices IS NOT NULL AND mcq_correct_choices IS NOT NULL)", create_type=False, name='mv_mcq_data_required'),
        sa.CheckConstraint(
            "(question_type = 'MCQ' AND marks = 1) OR "
            "(question_type = 'VSA' AND marks = 2) OR "
            "(question_type = 'SA' AND marks = 3) OR "
            "(question_type = 'LA' AND marks IN (5, 6))",
            create_type=False, name='mv_marks_match_type'
        ),
        sa.CheckConstraint("class IN ('X', 'XII')", create_type=False, name='mv_valid_class'),
        sa.CheckConstraint('version > 0', create_type=False, name='mv_valid_version'),
        sa.CheckConstraint('cbse_year IS NULL OR (cbse_year >= 2000 AND cbse_year <= 2100)', create_type=False, name='mv_valid_cbse_year'),
    )

    op.create_index('idx_questions_class_unit', 'questions', ['class', 'unit'])
    op.create_index('idx_questions_type', 'questions', ['question_type'])
    op.create_index('idx_questions_status', 'questions', ['status'], postgresql_where=sa.text("status = 'active'"))
    op.create_index('idx_questions_class_unit_type_status', 'questions', ['class', 'unit', 'question_type', 'status'],
                    postgresql_where=sa.text("status = 'active'"))
    op.create_index('idx_questions_tags', 'questions', ['tags'], postgresql_using='gin')

    # ------------------------------
    # 2.6 Exam Templates (depends on users)
    # ------------------------------
    op.create_table(
        'exam_templates',
        sa.Column('template_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('template_name', sa.String(255), nullable=False),
        sa.Column('class', sa.String(10), nullable=False),
        sa.Column('exam_type', postgresql.ENUM('board_exam', 'section_mcq', 'section_vsa', 'section_sa', 'unit_practice', create_type=False, name='mv_exam_type'), nullable=False),
        sa.Column('config', postgresql.JSONB(), nullable=False),
        sa.Column('specific_unit', sa.String(100)),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint("exam_type != 'unit_practice' OR specific_unit IS NOT NULL", create_type=False, name='mv_unit_practice_requires_unit'),
        sa.CheckConstraint("class IN ('X', 'XII')", create_type=False, name='mv_valid_class_level'),
    )

    op.create_index('idx_exam_templates_class_type', 'exam_templates', ['class', 'exam_type'])
    op.create_index('idx_exam_templates_active', 'exam_templates', ['is_active'],
                    postgresql_where=sa.text('is_active = true'))

    # ------------------------------
    # 2.7 Exam Instances (depends on users, exam_templates)
    # ------------------------------
    op.create_table(
        'exam_instances',
        sa.Column('exam_instance_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('student_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('exam_templates.template_id'), nullable=False),
        sa.Column('exam_snapshot', postgresql.JSONB(), nullable=False),
        sa.Column('exam_type', postgresql.ENUM('board_exam', 'section_mcq', 'section_vsa', 'section_sa', 'unit_practice', create_type=False, name='mv_exam_type'), nullable=False),
        sa.Column('class', sa.String(10), nullable=False),
        sa.Column('total_marks', sa.Integer(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('submitted_at', sa.DateTime(timezone=True)),
        sa.Column('time_taken_minutes', sa.Integer()),
        sa.Column('status', postgresql.ENUM('created', 'in_progress', 'submitted_mcq', 'pending_upload', 'uploaded', 'pending_evaluation', 'evaluated', create_type=False, name='mv_exam_status'),
                  nullable=False, server_default=sa.text("'created'")),
        sa.Column('mcq_score', sa.Numeric(6, 2), server_default=sa.text('0')),
        sa.Column('manual_score', sa.Numeric(6, 2), server_default=sa.text('0')),
        sa.Column('total_score', sa.Numeric(6, 2), server_default=sa.text('0')),
        sa.Column('percentage', sa.Numeric(5, 2)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint('submitted_at IS NULL OR submitted_at >= started_at', create_type=False, name='mv_valid_timing'),
        sa.CheckConstraint('total_score <= total_marks', create_type=False, name='mv_total_score_valid'),
        sa.CheckConstraint('percentage IS NULL OR (percentage >= 0 AND percentage <= 100)', create_type=False, name='mv_valid_percentage'),
        sa.CheckConstraint('mcq_score >= 0', create_type=False, name='mv_valid_mcq_score'),
        sa.CheckConstraint('manual_score >= 0', create_type=False, name='mv_valid_manual_score'),
        sa.CheckConstraint('total_score >= 0', create_type=False, name='mv_valid_total_score'),
    )

    op.create_index('idx_exam_instances_student', 'exam_instances', ['student_user_id'])
    op.create_index('idx_exam_instances_status', 'exam_instances', ['status'])
    op.create_index('idx_exam_instances_student_status', 'exam_instances', ['student_user_id', 'status'])
    op.create_index('idx_exam_instances_created', 'exam_instances', [sa.text('created_at DESC')])
    op.create_index('idx_exam_instances_submitted', 'exam_instances', [sa.text('submitted_at DESC')],
                    postgresql_where=sa.text('submitted_at IS NOT NULL'))
    op.create_index('idx_exam_instances_class_evaluated', 'exam_instances', ['class', sa.text('percentage DESC')],
                    postgresql_where=sa.text("status = 'evaluated'"))

    # ------------------------------
    # 2.8 Student MCQ Answers (depends on exam_instances)
    # ------------------------------
    op.create_table(
        'student_mcq_answers',
        sa.Column('answer_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('exam_instance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('exam_instances.exam_instance_id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_number', sa.Integer(), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('selected_choices', postgresql.JSONB(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('marks_awarded', sa.Numeric(5, 2), nullable=False),
        sa.Column('marks_possible', sa.Numeric(5, 2), nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('exam_instance_id', 'question_number', create_type=False, name='mv_unique_exam_question_answer'),
        sa.CheckConstraint('marks_awarded >= 0', create_type=False, name='mv_valid_marks_awarded'),
        sa.CheckConstraint('marks_possible > 0', create_type=False, name='mv_valid_marks_possible'),
        sa.CheckConstraint('question_number > 0', create_type=False, name='mv_valid_question_number'),
    )

    op.create_index('idx_mcq_answers_exam', 'student_mcq_answers', ['exam_instance_id'])
    op.create_index('idx_mcq_answers_question', 'student_mcq_answers', ['question_id'])

    # ------------------------------
    # 2.9 Answer Sheet Uploads (depends on exam_instances, users)
    # ------------------------------
    op.create_table(
        'answer_sheet_uploads',
        sa.Column('upload_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('exam_instance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('exam_instances.exam_instance_id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('s3_bucket', sa.String(255), nullable=False),
        sa.Column('s3_key', sa.Text(), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger()),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('questions_on_page', postgresql.JSONB()),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('exam_instance_id', 'page_number', create_type=False, name='mv_unique_exam_page'),
        sa.CheckConstraint('page_number > 0', create_type=False, name='mv_valid_page_number'),
        sa.CheckConstraint('file_size_bytes IS NULL OR file_size_bytes > 0', create_type=False, name='mv_valid_file_size'),
    )

    op.create_index('idx_answer_uploads_exam', 'answer_sheet_uploads', ['exam_instance_id'])
    op.create_index('idx_answer_uploads_s3_key', 'answer_sheet_uploads', ['s3_key'])

    # ------------------------------
    # 2.10 Unanswered Questions (depends on exam_instances)
    # ------------------------------
    op.create_table(
        'unanswered_questions',
        sa.Column('record_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('exam_instance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('exam_instances.exam_instance_id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_number', sa.Integer(), nullable=False),
        sa.Column('declared_unanswered', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('declared_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('exam_instance_id', 'question_number', create_type=False, name='mv_unique_exam_unanswered'),
        sa.CheckConstraint('question_number > 0', create_type=False, name='mv_valid_unanswered_question_number'),
    )

    op.create_index('idx_unanswered_exam', 'unanswered_questions', ['exam_instance_id'])

    # ------------------------------
    # 2.11 Evaluations (depends on exam_instances, users)
    # ------------------------------
    op.create_table(
        'evaluations',
        sa.Column('evaluation_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('exam_instance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('exam_instances.exam_instance_id'), nullable=False, unique=True),
        sa.Column('teacher_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('sla_deadline', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sla_hours_allocated', sa.Integer(), nullable=False),
        sa.Column('sla_breached', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('status', postgresql.ENUM('assigned', 'in_progress', 'completed', create_type=False, name='mv_evaluation_status'),
                  nullable=False, server_default=sa.text("'assigned'")),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('total_manual_marks', sa.Numeric(6, 2)),
        sa.Column('annotation_data', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint('sla_hours_allocated IN (24, 48)', create_type=False, name='mv_valid_sla_hours'),
        sa.CheckConstraint('total_manual_marks IS NULL OR total_manual_marks >= 0', create_type=False, name='mv_valid_total_manual_marks'),
    )

    op.create_index('idx_evaluations_teacher', 'evaluations', ['teacher_user_id'])
    op.create_index('idx_evaluations_status', 'evaluations', ['status'])
    op.create_index('idx_evaluations_teacher_status', 'evaluations', ['teacher_user_id', 'status'])
    op.create_index('idx_evaluations_sla_deadline', 'evaluations', ['sla_deadline', 'status'],
                    postgresql_where=sa.text("status != 'completed'"))

    # ------------------------------
    # 2.12 Question Marks (depends on evaluations, exam_instances)
    # ------------------------------
    op.create_table(
        'question_marks',
        sa.Column('mark_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('evaluation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('evaluations.evaluation_id', ondelete='CASCADE'), nullable=False),
        sa.Column('exam_instance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('exam_instances.exam_instance_id'), nullable=False),
        sa.Column('question_number', sa.Integer(), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_type', postgresql.ENUM('MCQ', 'VSA', 'SA', 'LA', create_type=False, name='mv_question_type'), nullable=False),
        sa.Column('unit', sa.String(100)),
        sa.Column('marks_awarded', sa.Numeric(5, 2), nullable=False),
        sa.Column('marks_possible', sa.Numeric(5, 2), nullable=False),
        sa.Column('teacher_comment', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('evaluation_id', 'question_number', create_type=False, name='mv_unique_evaluation_question'),
        sa.CheckConstraint('marks_awarded >= 0', create_type=False, name='mv_valid_question_marks_awarded'),
        sa.CheckConstraint('marks_possible > 0', create_type=False, name='mv_valid_question_marks_possible'),
        sa.CheckConstraint('marks_awarded <= marks_possible', create_type=False, name='mv_marks_within_limit'),
        sa.CheckConstraint('question_number > 0', create_type=False, name='mv_valid_mark_question_number'),
    )

    op.create_index('idx_question_marks_evaluation', 'question_marks', ['evaluation_id'])
    op.create_index('idx_question_marks_exam', 'question_marks', ['exam_instance_id'])
    op.create_index('idx_question_marks_question', 'question_marks', ['question_id'])
    op.create_index('idx_question_marks_unit', 'question_marks', ['unit'])

    # ------------------------------
    # 2.13 Audit Logs (depends on users)
    # ------------------------------
    op.create_table(
        'audit_logs',
        sa.Column('log_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id')),
        sa.Column('actor_role', postgresql.ENUM('student', 'parent', 'teacher', 'admin', create_type=False, name='mv_user_role')),
        sa.Column('actor_ip', postgresql.INET()),
        sa.Column('resource_type', sa.String(50)),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True)),
        sa.Column('event_data', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index('idx_audit_event_type', 'audit_logs', ['event_type'])
    op.create_index('idx_audit_actor', 'audit_logs', ['actor_user_id'])
    op.create_index('idx_audit_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_created', 'audit_logs', [sa.text('created_at DESC')])

    # Create immutability triggers for audit_logs
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Audit logs are immutable - cannot update or delete';
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER prevent_audit_update
            BEFORE UPDATE ON audit_logs
            FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();
    """)

    op.execute("""
        CREATE TRIGGER prevent_audit_delete
            BEFORE DELETE ON audit_logs
            FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();
    """)

    # ------------------------------
    # 2.14 Holidays (no dependencies)
    # ------------------------------
    op.create_table(
        'holidays',
        sa.Column('holiday_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('holiday_date', sa.Date(), unique=True, nullable=False),
        sa.Column('holiday_name', sa.String(255), nullable=False),
        sa.Column('holiday_type', sa.String(50)),
        sa.Column('is_working_day', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("holiday_date >= '2024-01-01'", create_type=False, name='mv_recent_or_future_holiday'),
    )

    op.create_index('idx_holidays_date', 'holidays', ['holiday_date'])

    # ------------------------------
    # 2.15 System Config (depends on users)
    # ------------------------------
    op.create_table(
        'system_config',
        sa.Column('config_key', sa.String(100), primary_key=True),
        sa.Column('config_value', postgresql.JSONB(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('config_value IS NOT NULL', create_type=False, name='mv_config_value_required'),
    )


def downgrade() -> None:
    # Drop triggers first
    op.execute('DROP TRIGGER IF EXISTS prevent_audit_delete ON audit_logs')
    op.execute('DROP TRIGGER IF EXISTS prevent_audit_update ON audit_logs')
    op.execute('DROP FUNCTION IF EXISTS prevent_audit_modification()')

    # Drop tables in reverse dependency order
    op.drop_table('system_config')
    op.drop_table('holidays')
    op.drop_table('audit_logs')
    op.drop_table('question_marks')
    op.drop_table('evaluations')
    op.drop_table('unanswered_questions')
    op.drop_table('answer_sheet_uploads')
    op.drop_table('student_mcq_answers')
    op.drop_table('exam_instances')
    op.drop_table('exam_templates')
    op.drop_table('questions')
    op.drop_table('subscriptions')
    op.drop_table('subscription_plans')
    op.drop_table('parent_student_mappings')
    op.drop_table('users')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS evaluation_status')
    op.execute('DROP TYPE IF EXISTS exam_status')
    op.execute('DROP TYPE IF EXISTS exam_type')
    op.execute('DROP TYPE IF EXISTS question_status')
    op.execute('DROP TYPE IF EXISTS question_difficulty')
    op.execute('DROP TYPE IF EXISTS question_type')
    op.execute('DROP TYPE IF EXISTS subscription_status')
    op.execute('DROP TYPE IF EXISTS plan_type')
    op.execute('DROP TYPE IF EXISTS relationship_type')
    op.execute('DROP TYPE IF EXISTS user_role')

    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS btree_gist')
