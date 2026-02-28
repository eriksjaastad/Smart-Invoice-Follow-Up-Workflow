"""
System state model for global operational flags.
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class SystemState(Base):
    """Singleton table for global system flags."""

    __tablename__ = "system_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    system_paused: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<SystemState(id={self.id}, system_paused={self.system_paused})>"
