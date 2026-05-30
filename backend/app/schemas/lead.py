"""Lead capture schemas."""
from pydantic import BaseModel, EmailStr, Field


class LeadCreate(BaseModel):
    """Public lead capture request."""

    email: EmailStr
    source: str = Field(default="landing", min_length=1, max_length=80)
    intent: str | None = Field(default=None, max_length=240)


class LeadResponse(BaseModel):
    """Public lead capture response."""

    status: str = "success"
    message: str
