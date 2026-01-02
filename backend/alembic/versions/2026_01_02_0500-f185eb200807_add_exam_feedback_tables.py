"""add_exam_feedback_tables

Revision ID: f185eb200807
Revises: 0d8157956977
Create Date: 2026-01-02 05:00:26.723454+05:30

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f185eb200807"
down_revision = "0d8157956977"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create exam_feedbacks table
    op.create_table(
        "exam_feedbacks",
        sa.Column("feedback_id", sa.UUID(), nullable=False),
        sa.Column("evaluation_id", sa.UUID(), nullable=False),
        sa.Column("exam_instance_id", sa.UUID(), nullable=False),
        sa.Column("student_user_id", sa.UUID(), nullable=False),
        sa.Column("teacher_user_id", sa.UUID(), nullable=True),
        sa.Column("overall_feedback", sa.Text(), nullable=True),
        sa.Column("total_question_feedbacks", sa.Integer(), default=0),
        sa.Column("pending_clarifications", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["evaluation_id"], ["evaluations.evaluation_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["exam_instance_id"], ["exam_instances.exam_instance_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["student_user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_user_id"], ["users.user_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("feedback_id"),
    )
    op.create_index(
        "ix_exam_feedbacks_evaluation_id", "exam_feedbacks", ["evaluation_id"], unique=True
    )
    op.create_index(
        "ix_exam_feedbacks_exam_instance_id", "exam_feedbacks", ["exam_instance_id"], unique=False
    )
    op.create_index(
        "ix_exam_feedbacks_student_user_id", "exam_feedbacks", ["student_user_id"], unique=False
    )
    op.create_index(
        "ix_exam_feedbacks_teacher_user_id", "exam_feedbacks", ["teacher_user_id"], unique=False
    )

    # Create question_feedbacks table
    op.create_table(
        "question_feedbacks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("exam_feedback_id", sa.UUID(), nullable=False),
        sa.Column("question_number", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, default="open"),
        # Teacher feedback
        sa.Column("teacher_feedback", sa.Text(), nullable=True),
        sa.Column("feedback_type", sa.String(length=20), default="general"),
        sa.Column("feedback_created_at", sa.DateTime(timezone=True), nullable=True),
        # Student clarification
        sa.Column("student_question", sa.Text(), nullable=True),
        sa.Column("student_attachment_url", sa.String(length=500), nullable=True),
        sa.Column("student_question_at", sa.DateTime(timezone=True), nullable=True),
        # Teacher response
        sa.Column("teacher_response", sa.Text(), nullable=True),
        sa.Column("teacher_response_attachment_url", sa.String(length=500), nullable=True),
        sa.Column("teacher_response_at", sa.DateTime(timezone=True), nullable=True),
        # AI suggestion fields (for future use)
        sa.Column("ai_suggested_feedback", sa.Text(), nullable=True),
        sa.Column("ai_confidence_score", sa.Float(), nullable=True),
        sa.Column("teacher_used_ai_suggestion", sa.Boolean(), default=False),
        sa.Column("ai_model_version", sa.String(length=50), nullable=True),
        sa.Column("ai_generated_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["exam_feedback_id"], ["exam_feedbacks.feedback_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_question_feedbacks_exam_feedback_id",
        "question_feedbacks",
        ["exam_feedback_id"],
        unique=False,
    )
    op.create_index(
        "ix_question_feedbacks_question_id",
        "question_feedbacks",
        ["question_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_question_feedbacks_question_id", table_name="question_feedbacks")
    op.drop_index("ix_question_feedbacks_exam_feedback_id", table_name="question_feedbacks")
    op.drop_table("question_feedbacks")

    op.drop_index("ix_exam_feedbacks_teacher_user_id", table_name="exam_feedbacks")
    op.drop_index("ix_exam_feedbacks_student_user_id", table_name="exam_feedbacks")
    op.drop_index("ix_exam_feedbacks_exam_instance_id", table_name="exam_feedbacks")
    op.drop_index("ix_exam_feedbacks_evaluation_id", table_name="exam_feedbacks")
    op.drop_table("exam_feedbacks")
