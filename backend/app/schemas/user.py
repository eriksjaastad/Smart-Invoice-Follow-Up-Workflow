"""
User Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    business_name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    """Schema for creating a new user."""
    auth0_user_id: str = Field(..., min_length=1, max_length=255, description="Auth0 user identifier")


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    business_name: Optional[str] = Field(None, min_length=1, max_length=255)
    sheet_id: Optional[str] = Field(None, max_length=255)
    active: Optional[bool] = None


class User(UserBase):
    """Schema for user response (full user object)."""
    id: UUID
    auth0_user_id: str
    sheet_id: Optional[str] = None
    google_email: Optional[str] = None
    google_connected: bool = False
    active: bool
    plan: str
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    created_at: datetime
    last_run_at: Optional[datetime] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def compute_google_connected(cls, data):
        """Compute google_connected from ORM model attributes."""
        # When validating from an ORM object (has attributes, not dict keys)
        if hasattr(data, "google_refresh_token_encrypted"):
            # It's an ORM model object — read attributes
            data = {
                "id": data.id,
                "auth0_user_id": data.auth0_user_id,
                "email": data.email,
                "name": data.name,
                "business_name": data.business_name,
                "sheet_id": data.sheet_id,
                "google_email": data.google_email,
                "google_connected": (
                    data.google_refresh_token_encrypted is not None
                    and not data.google_token_revoked
                ),
                "active": data.active,
                "plan": data.plan,
                "stripe_customer_id": data.stripe_customer_id,
                "stripe_subscription_id": data.stripe_subscription_id,
                "created_at": data.created_at,
                "last_run_at": data.last_run_at,
                "updated_at": data.updated_at,
            }
        return data


class UserConfig(BaseModel):
    """
    Schema for user config API response.
    Used by daily processing to get user settings.
    """
    user_id: UUID
    email: EmailStr
    sender_name: str
    business_name: str
    sheet_id: str
    active: bool
    paused: bool  # Global kill switch status
    plan: str
    invoice_limit: int  # 3 for free, 100 for paid

    model_config = ConfigDict(from_attributes=True)
