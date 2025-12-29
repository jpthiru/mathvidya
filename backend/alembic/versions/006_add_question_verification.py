"""Add verification fields to questions table

Revision ID: 006
Revises: 005
Create Date: 2025-12-28

Adds is_verified and verified_by_user_id columns for batch question verification.
Marks all existing questions as verified.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_verified column with default False
    op.add_column(
        'questions',
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false')
    )

    # Add verified_by_user_id column (nullable - only set when verified)
    op.add_column(
        'questions',
        sa.Column('verified_by_user_id', UUID(as_uuid=True), nullable=True)
    )

    # Add verified_at timestamp column
    op.add_column(
        'questions',
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True)
    )

    # Add foreign key constraint for verified_by_user_id
    op.create_foreign_key(
        'fk_questions_verified_by_user',
        'questions',
        'users',
        ['verified_by_user_id'],
        ['user_id']
    )

    # Create index for faster filtering of unverified questions
    op.create_index(
        'ix_questions_is_verified',
        'questions',
        ['is_verified']
    )

    # Mark all existing questions as verified (they were manually created)
    op.execute("""
        UPDATE questions
        SET is_verified = true,
            verified_at = NOW()
        WHERE is_verified = false
    """)


def downgrade() -> None:
    # Drop the index
    op.drop_index('ix_questions_is_verified', table_name='questions')

    # Drop the foreign key constraint
    op.drop_constraint('fk_questions_verified_by_user', 'questions', type_='foreignkey')

    # Remove the columns
    op.drop_column('questions', 'verified_at')
    op.drop_column('questions', 'verified_by_user_id')
    op.drop_column('questions', 'is_verified')
