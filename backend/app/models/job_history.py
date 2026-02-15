"""
Job history database model.
"""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class JobHistory(Base):
    """Job history model for tracking Make.com scenario runs."""
    
    __tablename__ = "job_history"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to user
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Job execution details
    run_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    invoices_checked: Mapped[int] = mapped_column(Integer, nullable=False)
    drafts_created: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Financial tracking (added per tasks.md requirement)
    total_outstanding_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Error tracking (JSONB for flexible error storage)
    errors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    # Performance tracking
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="job_history")
    
    def __repr__(self) -> str:
        return f"<JobHistory(id={self.id}, user_id={self.user_id}, run_at={self.run_at})>"

