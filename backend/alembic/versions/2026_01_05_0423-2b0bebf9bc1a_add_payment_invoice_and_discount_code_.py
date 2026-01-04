"""Add payment, invoice, and discount code tables

Revision ID: 2b0bebf9bc1a
Revises: 64677cd5158f
Create Date: 2026-01-05 04:23:02.214081+05:30

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM


# revision identifiers, used by Alembic.
revision = "2b0bebf9bc1a"
down_revision = "64677cd5158f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create discount_codes table
    op.create_table(
        'discount_codes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('discount_type', sa.String(20), nullable=False),
        sa.Column('discount_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('valid_from', sa.String(100), nullable=False),
        sa.Column('valid_until', sa.String(100), nullable=False),
        sa.Column('max_uses', sa.Integer()),
        sa.Column('uses_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_uses_per_user', sa.Integer(), server_default='1'),
        sa.Column('applicable_plans', sa.Text()),
        sa.Column('min_purchase_amount', sa.Numeric(10, 2)),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_by', sa.UUID()),
        sa.Column('created_at', sa.String(100)),
        sa.Column('updated_at', sa.String(100)),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_discount_codes_code', 'discount_codes', ['code'], unique=True)
    op.create_index('ix_discount_codes_is_active', 'discount_codes', ['is_active'])
    op.create_index('ix_discount_codes_valid_until', 'discount_codes', ['valid_until'])
    op.create_index('idx_discount_code_active_valid', 'discount_codes', ['is_active', 'valid_until'])

    # Reference existing ENUM type
    plan_type_enum = ENUM(name='mv_plan_type', create_type=False)

    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('plan_type', plan_type_enum, nullable=False),
        sa.Column('razorpay_order_id', sa.String(100)),
        sa.Column('razorpay_payment_id', sa.String(100)),
        sa.Column('razorpay_signature', sa.String(200)),
        sa.Column('amount_inr', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='INR'),
        sa.Column('status', sa.String(20), nullable=False, server_default='created'),
        sa.Column('payment_method', sa.String(50)),
        sa.Column('payment_method_details', sa.JSON()),
        sa.Column('discount_code', sa.String(50)),
        sa.Column('discount_amount_inr', sa.Numeric(10, 2), server_default='0'),
        sa.Column('base_amount_inr', sa.Numeric(10, 2)),
        sa.Column('gst_amount_inr', sa.Numeric(10, 2)),
        sa.Column('cgst_inr', sa.Numeric(10, 2)),
        sa.Column('sgst_inr', sa.Numeric(10, 2)),
        sa.Column('igst_inr', sa.Numeric(10, 2)),
        sa.Column('invoice_id', sa.UUID()),
        sa.Column('is_refunded', sa.String(10), server_default='false'),
        sa.Column('refund_amount_inr', sa.Numeric(10, 2), server_default='0'),
        sa.Column('refund_reason', sa.Text()),
        sa.Column('refunded_at', sa.String(100)),
        sa.Column('razorpay_order_response', sa.JSON()),
        sa.Column('razorpay_payment_response', sa.JSON()),
        sa.Column('razorpay_webhook_data', sa.JSON()),
        sa.Column('created_at', sa.String(100)),
        sa.Column('updated_at', sa.String(100)),
        sa.Column('payment_completed_at', sa.String(100)),
        sa.Column('user_ip', sa.String(50)),
        sa.Column('user_agent', sa.String(500)),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['plan_type'], ['subscription_plans.plan_type'])
    )
    op.create_index('ix_payments_user_id', 'payments', ['user_id'])
    op.create_index('ix_payments_razorpay_order_id', 'payments', ['razorpay_order_id'], unique=True)
    op.create_index('ix_payments_razorpay_payment_id', 'payments', ['razorpay_payment_id'], unique=True)
    op.create_index('ix_payments_status', 'payments', ['status'])
    op.create_index('ix_payments_discount_code', 'payments', ['discount_code'])
    op.create_index('ix_payments_created_at', 'payments', ['created_at'])
    op.create_index('idx_payment_user_status', 'payments', ['user_id', 'status'])

    # Create invoices table
    op.create_table(
        'invoices',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('invoice_number', sa.String(50), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('payment_id', sa.UUID(), nullable=False),
        sa.Column('subscription_id', sa.UUID()),
        sa.Column('invoice_date', sa.String(100), nullable=False),
        sa.Column('customer_name', sa.String(200), nullable=False),
        sa.Column('customer_email', sa.String(200), nullable=False),
        sa.Column('customer_phone', sa.String(20)),
        sa.Column('customer_address', sa.Text()),
        sa.Column('customer_state', sa.String(100)),
        sa.Column('item_description', sa.Text(), nullable=False),
        sa.Column('item_quantity', sa.String(10), server_default='1'),
        sa.Column('item_unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('subtotal_inr', sa.Numeric(10, 2), nullable=False),
        sa.Column('discount_inr', sa.Numeric(10, 2), server_default='0'),
        sa.Column('taxable_amount_inr', sa.Numeric(10, 2), nullable=False),
        sa.Column('cgst_rate', sa.Numeric(5, 2), server_default='9.00'),
        sa.Column('cgst_amount_inr', sa.Numeric(10, 2), server_default='0'),
        sa.Column('sgst_rate', sa.Numeric(5, 2), server_default='9.00'),
        sa.Column('sgst_amount_inr', sa.Numeric(10, 2), server_default='0'),
        sa.Column('igst_rate', sa.Numeric(5, 2), server_default='18.00'),
        sa.Column('igst_amount_inr', sa.Numeric(10, 2), server_default='0'),
        sa.Column('total_gst_inr', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_amount_inr', sa.Numeric(10, 2), nullable=False),
        sa.Column('company_name', sa.String(200), server_default='Quantvin Technologies'),
        sa.Column('company_gst', sa.String(20), server_default='33ABXPL0022H1ZU'),
        sa.Column('company_address', sa.Text()),
        sa.Column('company_state', sa.String(100), server_default='Tamil Nadu'),
        sa.Column('pdf_url', sa.String(500)),
        sa.Column('created_at', sa.String(100)),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id']),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.subscription_id'])
    )
    op.create_index('ix_invoices_invoice_number', 'invoices', ['invoice_number'], unique=True)
    op.create_index('ix_invoices_user_id', 'invoices', ['user_id'])
    op.create_index('ix_invoices_payment_id', 'invoices', ['payment_id'], unique=True)
    op.create_index('idx_invoice_user_date', 'invoices', ['user_id', 'invoice_date'])

    # Create discount_code_usage table
    op.create_table(
        'discount_code_usage',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('discount_code_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('payment_id', sa.UUID(), nullable=False),
        sa.Column('discount_amount_inr', sa.String(20), nullable=False),
        sa.Column('used_at', sa.String(100)),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['discount_code_id'], ['discount_codes.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'])
    )
    op.create_index('ix_discount_code_usage_discount_code_id', 'discount_code_usage', ['discount_code_id'])
    op.create_index('ix_discount_code_usage_user_id', 'discount_code_usage', ['user_id'])
    op.create_index('ix_discount_code_usage_used_at', 'discount_code_usage', ['used_at'])
    op.create_index('idx_discount_usage_user_code', 'discount_code_usage', ['user_id', 'discount_code_id'])

    # Add foreign key from payments.invoice_id to invoices.id (circular dependency resolved by deferring)
    op.create_foreign_key('fk_payments_invoice_id', 'payments', 'invoices', ['invoice_id'], ['id'])

    # Insert initial discount codes for testing
    from datetime import datetime, timedelta
    import uuid

    valid_until = (datetime.utcnow() + timedelta(days=90)).isoformat()

    op.execute(f"""
        INSERT INTO discount_codes (id, code, description, discount_type, discount_value, valid_from, valid_until, is_active, created_at)
        VALUES
        ('{uuid.uuid4()}', 'LAUNCH50', 'Introductory launch offer - 50% off', 'percentage', 50.00, '{datetime.utcnow().isoformat()}', '{valid_until}', true, '{datetime.utcnow().isoformat()}'),
        ('{uuid.uuid4()}', 'WELCOME250', 'Welcome discount - ₹250 off Basic plan', 'fixed', 250.00, '{datetime.utcnow().isoformat()}', '{valid_until}', true, '{datetime.utcnow().isoformat()}'),
        ('{uuid.uuid4()}', 'MCQPRO400', 'MCQ Pro discount - ₹400 off Premium MCQ', 'fixed', 400.00, '{datetime.utcnow().isoformat()}', '{valid_until}', true, '{datetime.utcnow().isoformat()}')
    """)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('discount_code_usage')
    op.drop_table('invoices')
    op.drop_table('payments')
    op.drop_table('discount_codes')
