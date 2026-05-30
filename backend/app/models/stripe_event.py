"""Stripe webhook event idempotency model."""
from datetime import UTC, datetime

from sqlalchemy import DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class StripeEvent(Base):
    """Processed Stripe webhook event id for idempotency."""

    __tablename__ = "stripe_events"

    event_id: Mapped[str] = mapped_column(Text, primary_key=True)
    event_type: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<StripeEvent(event_id={self.event_id}, event_type={self.event_type})>"
