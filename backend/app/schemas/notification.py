"""
Notification Pydantic schemas for error notifications.
"""
from pydantic import BaseModel, Field


class NotificationCheckRequest(BaseModel):
    """Request schema for checking failures (cron endpoint)."""
    secret: str = Field(..., description="Cron secret for authentication")


class NotificationCheckResponse(BaseModel):
    """Response schema for notification check endpoint."""
    success: bool
    users_checked: int = Field(..., ge=0, description="Number of users checked")
    failures_detected: int = Field(default=0, ge=0, description="Number of users with consecutive failures")
    notifications_sent: int = Field(default=0, ge=0, description="Number of notifications sent")
    notifications_failed: int = Field(default=0, ge=0, description="Number of failed notification sends")
    message: str

