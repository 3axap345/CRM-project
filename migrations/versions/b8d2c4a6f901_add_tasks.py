"""add tasks

Revision ID: b8d2c4a6f901
Revises: 7a4f6c2d9b10
Create Date: 2026-08-20 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b8d2c4a6f901'
down_revision = '7a4f6c2d9b10'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=160), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=50), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=True),
        sa.Column('deal_id', sa.Integer(), nullable=True),
        sa.Column('assigned_to', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "status IN ('todo', 'in_progress', 'done')",
            name='ck_tasks_status_valid',
        ),
        sa.CheckConstraint(
            "priority IN ('low', 'medium', 'high')",
            name='ck_tasks_priority_valid',
        ),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], name='fk_task_assigned_user', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], name='fk_task_client', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], name='fk_task_deal', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tasks_assigned_to', 'tasks', ['assigned_to'], unique=False)
    op.create_index('ix_tasks_client_id', 'tasks', ['client_id'], unique=False)
    op.create_index('ix_tasks_deal_id', 'tasks', ['deal_id'], unique=False)
    op.create_index('ix_tasks_due_date', 'tasks', ['due_date'], unique=False)
    op.create_index('ix_tasks_priority', 'tasks', ['priority'], unique=False)
    op.create_index('ix_tasks_status', 'tasks', ['status'], unique=False)


def downgrade():
    op.drop_index('ix_tasks_status', table_name='tasks')
    op.drop_index('ix_tasks_priority', table_name='tasks')
    op.drop_index('ix_tasks_due_date', table_name='tasks')
    op.drop_index('ix_tasks_deal_id', table_name='tasks')
    op.drop_index('ix_tasks_client_id', table_name='tasks')
    op.drop_index('ix_tasks_assigned_to', table_name='tasks')
    op.drop_table('tasks')
