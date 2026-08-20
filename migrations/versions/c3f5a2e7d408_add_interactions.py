"""add interactions

Revision ID: c3f5a2e7d408
Revises: b8d2c4a6f901
Create Date: 2026-08-20 14:30:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'c3f5a2e7d408'
down_revision = 'b8d2c4a6f901'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'interactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "type IN ('note', 'call', 'meeting', 'email')",
            name='ck_interactions_type_valid',
        ),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], name='fk_interaction_author', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], name='fk_interaction_client', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_interactions_author_id', 'interactions', ['author_id'], unique=False)
    op.create_index('ix_interactions_client_id', 'interactions', ['client_id'], unique=False)
    op.create_index('ix_interactions_type', 'interactions', ['type'], unique=False)


def downgrade():
    op.drop_index('ix_interactions_type', table_name='interactions')
    op.drop_index('ix_interactions_client_id', table_name='interactions')
    op.drop_index('ix_interactions_author_id', table_name='interactions')
    op.drop_table('interactions')
