"""Update MCQ data check constraint

Revision ID: 004
Revises: 003
Create Date: 2025-12-25

Update the mv_mcq_data_required constraint to use new column names (options, correct_option)
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old constraint
    op.drop_constraint("mv_mcq_data_required", "questions", type_="check")

    # Create the new constraint with updated column names
    op.create_check_constraint(
        "mv_mcq_data_required",
        "questions",
        "question_type != 'MCQ' OR (options IS NOT NULL AND correct_option IS NOT NULL)"
    )


def downgrade() -> None:
    # Drop the new constraint
    op.drop_constraint("mv_mcq_data_required", "questions", type_="check")

    # Recreate the old constraint
    op.create_check_constraint(
        "mv_mcq_data_required",
        "questions",
        "question_type != 'MCQ' OR (mcq_choices IS NOT NULL AND mcq_correct_choices IS NOT NULL)"
    )
