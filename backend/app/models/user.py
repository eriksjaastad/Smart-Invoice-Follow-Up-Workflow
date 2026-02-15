"""
User database model.
"""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, String, Text, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    """User model representing a SaaS customer."""
    
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Auth0 integration
    auth0_user_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    
    # User information
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    business_name: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Google Sheets and Make.com integration
    sheet_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    make_scenario_id: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    
    # Account status
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    plan: Mapped[str] = mapped_column(
        String(10), 
        default='free', 
        nullable=False,
        server_default='free'
    )
    
    # Stripe integration
    stripe_customer_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    job_history: Mapped[list["JobHistory"]] = relationship(
        "JobHistory", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint("plan IN ('free', 'paid')", name='check_plan_values'),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, plan={self.plan})>"

