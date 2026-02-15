"""Initial schema: users and job_history tables

Revision ID: 001
Revises: 
Create Date: 2026-02-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('auth0_user_id', sa.Text(), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('business_name', sa.Text(), nullable=False),
        sa.Column('sheet_id', sa.Text(), nullable=True),
        sa.Column('make_scenario_id', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('plan', sa.String(length=10), server_default=sa.text("'free'"), nullable=False),
        sa.Column('stripe_customer_id', sa.Text(), nullable=True),
        sa.Column('stripe_subscription_id', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('auth0_user_id'),
        sa.UniqueConstraint('email'),
        sa.CheckConstraint("plan IN ('free', 'paid')", name='check_plan_values')
    )
    
    # Create indexes for users table
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_auth0', 'users', ['auth0_user_id'])
    op.create_index('idx_users_make_scenario', 'users', ['make_scenario_id'])
    
    # Create job_history table
    op.create_table(
        'job_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('invoices_checked', sa.Integer(), nullable=False),
        sa.Column('drafts_created', sa.Integer(), nullable=False),
        sa.Column('total_outstanding_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('errors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for job_history table
    op.create_index('idx_job_history_user', 'job_history', ['user_id'])
    op.create_index('idx_job_history_run_at', 'job_history', ['run_at'])


def downgrade() -> None:
    # Drop job_history table and indexes
    op.drop_index('idx_job_history_run_at', table_name='job_history')
    op.drop_index('idx_job_history_user', table_name='job_history')
    op.drop_table('job_history')
    
    # Drop users table and indexes
    op.drop_index('idx_users_make_scenario', table_name='users')
    op.drop_index('idx_users_auth0', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')

