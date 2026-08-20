"""add deals

Revision ID: 7a4f6c2d9b10
Revises: 03f346e8e9e0
Create Date: 2026-08-20 13:30:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = '7a4f6c2d9b10'
down_revision = '03f346e8e9e0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'deals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=160), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('manager_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "status IN ('new', 'qualified', 'proposal', 'negotiation', 'won', 'lost')",
            name='ck_deals_status_valid',
        ),
        sa.CheckConstraint('amount >= 0', name='ck_deals_amount_non_negative'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], name='fk_deal_client', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['manager_id'], ['users.id'], name='fk_deal_manager', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_deals_client_id', 'deals', ['client_id'], unique=False)
    op.create_index('ix_deals_manager_id', 'deals', ['manager_id'], unique=False)
    op.create_index('ix_deals_status', 'deals', ['status'], unique=False)


def downgrade():
    op.drop_index('ix_deals_status', table_name='deals')
    op.drop_index('ix_deals_manager_id', table_name='deals')
    op.drop_index('ix_deals_client_id', table_name='deals')
    op.drop_table('deals')
