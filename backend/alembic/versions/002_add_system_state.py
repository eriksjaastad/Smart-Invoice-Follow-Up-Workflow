"""Add system_state table for global kill switch

Revision ID: 002
Revises: 001
Create Date: 2026-02-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "system_state",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "system_paused",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.execute("INSERT INTO system_state (system_paused) VALUES (false)")


def downgrade() -> None:
    op.drop_table("system_state")
