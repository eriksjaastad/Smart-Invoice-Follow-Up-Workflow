"""
System state schemas for request/response validation.
"""
from pydantic import BaseModel, Field


class SystemStatus(BaseModel):
    """Global system status response."""
    paused: bool


class SystemUpdateRequest(BaseModel):
    """Request to update the global paused flag."""
    paused: bool
    secret: str = Field(..., min_length=1)
