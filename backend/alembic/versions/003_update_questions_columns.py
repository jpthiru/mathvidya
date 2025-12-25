"""Update Question model columns

Revision ID: 003
Revises: 002
Create Date: 2025-12-25

Add chapter, options, correct_option, model_answer, marking_scheme columns
Rename created_by to created_by_user_id
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to questions table
    op.add_column("questions", sa.Column("chapter", sa.String(length=100), nullable=True))
    op.add_column("questions", sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("questions", sa.Column("correct_option", sa.String(length=1), nullable=True))
    op.add_column("questions", sa.Column("model_answer", sa.Text(), nullable=True))
    op.add_column("questions", sa.Column("marking_scheme", sa.Text(), nullable=True))
    op.add_column("questions", sa.Column("created_by_user_id", sa.UUID(), nullable=True))

    # Copy data from created_by to created_by_user_id
    op.execute("UPDATE questions SET created_by_user_id = created_by WHERE created_by IS NOT NULL")

    # Create foreign key for created_by_user_id
    op.create_foreign_key(
        "fk_questions_created_by_user_id",
        "questions",
        "users",
        ["created_by_user_id"],
        ["user_id"]
    )


def downgrade() -> None:
    # Drop foreign key
    op.drop_constraint("fk_questions_created_by_user_id", "questions", type_="foreignkey")

    # Drop new columns
    op.drop_column("questions", "created_by_user_id")
    op.drop_column("questions", "marking_scheme")
    op.drop_column("questions", "model_answer")
    op.drop_column("questions", "correct_option")
    op.drop_column("questions", "options")
    op.drop_column("questions", "chapter")
