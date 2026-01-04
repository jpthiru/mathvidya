"""Add promo codes and site feedback tables

Revision ID: 64677cd5158f
Revises: f185eb200807
Create Date: 2026-01-04 07:22:22.193322+05:30

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "64677cd5158f"
down_revision = "f185eb200807"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create promo_codes table
    op.create_table(
        "promo_codes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("promo_type", sa.String(length=30), nullable=False),
        sa.Column("discount_percentage", sa.Float(), nullable=True),
        sa.Column("discount_amount", sa.Float(), nullable=True),
        sa.Column("free_days", sa.Integer(), nullable=True),
        sa.Column("free_months", sa.Integer(), nullable=True),
        sa.Column("applicable_plans", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("current_uses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_uses_per_user", sa.Integer(), nullable=True, server_default="1"),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("new_users_only", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("minimum_order_value", sa.Float(), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_promo_codes_code"), "promo_codes", ["code"], unique=True)

    # Create promo_code_usages table
    op.create_table(
        "promo_code_usages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("promo_code_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("subscription_id", sa.UUID(), nullable=True),
        sa.Column("original_amount", sa.Float(), nullable=True),
        sa.Column("discount_applied", sa.Float(), nullable=True),
        sa.Column("final_amount", sa.Float(), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_promo_code_usages_promo_code_id"),
        "promo_code_usages",
        ["promo_code_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_promo_code_usages_user_id"), "promo_code_usages", ["user_id"], unique=False
    )

    # Create site_feedbacks table
    op.create_table(
        "site_feedbacks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(length=30), nullable=False, server_default="other"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("page_url", sa.String(length=500), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="new"),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.UUID(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_site_feedbacks_user_id"), "site_feedbacks", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_site_feedbacks_user_id"), table_name="site_feedbacks")
    op.drop_table("site_feedbacks")
    op.drop_index(op.f("ix_promo_code_usages_user_id"), table_name="promo_code_usages")
    op.drop_index(op.f("ix_promo_code_usages_promo_code_id"), table_name="promo_code_usages")
    op.drop_table("promo_code_usages")
    op.drop_index(op.f("ix_promo_codes_code"), table_name="promo_codes")
    op.drop_table("promo_codes")
