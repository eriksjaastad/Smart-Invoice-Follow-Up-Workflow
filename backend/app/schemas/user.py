"""
User Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


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
    make_scenario_id: Optional[str] = Field(None, max_length=255)
    active: Optional[bool] = None


class User(UserBase):
    """Schema for user response (full user object)."""
    id: UUID
    auth0_user_id: str
    sheet_id: Optional[str] = None
    make_scenario_id: Optional[str] = None
    active: bool
    plan: str
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    created_at: datetime
    last_run_at: Optional[datetime] = None
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserConfig(BaseModel):
    """
    Schema for Make.com config API response.
    This is what Make.com scenarios fetch via GET /api/users/{user_id}/config
    """
    user_id: UUID
    email: EmailStr
    sender_name: str
    business_name: str
    sheet_id: str
    active: bool
    paused: bool  # Global kill switch status
    backend_url: str
    plan: str
    invoice_limit: int  # 3 for free, 100 for paid
    
    model_config = ConfigDict(from_attributes=True)
