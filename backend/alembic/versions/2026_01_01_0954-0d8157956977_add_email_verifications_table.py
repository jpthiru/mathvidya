"""Add email_verifications table

Revision ID: 0d8157956977
Revises: 007
Create Date: 2026-01-01 09:54:47.373805+05:30

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0d8157956977"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create email_verifications table
    op.create_table(
        "email_verifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=6), nullable=False),
        sa.Column("verification_type", sa.String(length=20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=True, default=0),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_email_verifications_code_email",
        "email_verifications",
        ["code", "email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_email_verifications_email"),
        "email_verifications",
        ["email"],
        unique=False,
    )
    op.create_index(
        "ix_email_verifications_email_type",
        "email_verifications",
        ["email", "verification_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_email_verifications_email_type", table_name="email_verifications")
    op.drop_index(op.f("ix_email_verifications_email"), table_name="email_verifications")
    op.drop_index("ix_email_verifications_code_email", table_name="email_verifications")
    op.drop_table("email_verifications")
