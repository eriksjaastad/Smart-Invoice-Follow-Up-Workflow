"""Add Stripe webhook idempotency table

Revision ID: 004
Revises: 003
Create Date: 2026-05-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stripe_events",
        sa.Column("event_id", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("idx_stripe_events_type", "stripe_events", ["event_type"])
    op.create_index("idx_stripe_events_processed_at", "stripe_events", ["processed_at"])


def downgrade() -> None:
    op.drop_index("idx_stripe_events_processed_at", table_name="stripe_events")
    op.drop_index("idx_stripe_events_type", table_name="stripe_events")
    op.drop_table("stripe_events")
