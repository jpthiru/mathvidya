"""Add Class IX and XI support

Revision ID: a1b2c3d4e5f6
Revises: 2b0bebf9bc1a
Create Date: 2026-02-01 10:00:00.000000+05:30

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '2b0bebf9bc1a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old check constraints
    op.drop_constraint('mv_valid_class', 'questions', type_='check')
    op.drop_constraint('mv_valid_class_level', 'exam_templates', type_='check')

    # Create new check constraints with IX and XI added
    op.create_check_constraint(
        'mv_valid_class',
        'questions',
        "class IN ('IX', 'X', 'XI', 'XII')"
    )
    op.create_check_constraint(
        'mv_valid_class_level',
        'exam_templates',
        "class IN ('IX', 'X', 'XI', 'XII')"
    )


def downgrade() -> None:
    # Drop new constraints
    op.drop_constraint('mv_valid_class', 'questions', type_='check')
    op.drop_constraint('mv_valid_class_level', 'exam_templates', type_='check')

    # Restore old constraints
    op.create_check_constraint(
        'mv_valid_class',
        'questions',
        "class IN ('X', 'XII')"
    )
    op.create_check_constraint(
        'mv_valid_class_level',
        'exam_templates',
        "class IN ('X', 'XII')"
    )
