"""Make template_id nullable for unit practice exams

Revision ID: 005
Revises: 004
Create Date: 2025-12-26

Unit practice exams don't use templates, so template_id must be nullable.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make template_id nullable
    op.alter_column(
        'exam_instances',
        'template_id',
        nullable=True
    )


def downgrade() -> None:
    # Revert to NOT NULL (only safe if no NULL values exist)
    op.alter_column(
        'exam_instances',
        'template_id',
        nullable=False
    )
