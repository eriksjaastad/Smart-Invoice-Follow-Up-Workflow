"""Add billing_last_event_at to users for Stripe event ordering

Revision ID: 003
Revises: 002
Create Date: 2026-03-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('billing_last_event_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'billing_last_event_at')
