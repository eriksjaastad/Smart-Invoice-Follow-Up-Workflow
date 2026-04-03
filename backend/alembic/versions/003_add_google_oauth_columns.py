"""Add Google OAuth columns to users table

Revision ID: 003
Revises: 002
Create Date: 2026-03-16

Replaces Make.com integration with direct Google OAuth.
Adds columns for storing encrypted refresh tokens and connection state.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("google_refresh_token_encrypted", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("google_email", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("google_connected_at", sa.DateTime(), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "google_token_revoked",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "google_token_revoked")
    op.drop_column("users", "google_connected_at")
    op.drop_column("users", "google_email")
    op.drop_column("users", "google_refresh_token_encrypted")
