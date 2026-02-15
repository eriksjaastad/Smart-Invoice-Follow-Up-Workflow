"""
Digest Pydantic schemas for weekly email digest functionality.
"""
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class DigestData(BaseModel):
    """
    Schema for weekly digest email data.
    Contains aggregated job history data for a user's weekly summary email.
    """
    user_id: UUID
    user_name: str = Field(..., description="User's name for email greeting")
    user_email: EmailStr = Field(..., description="User's email address")
    business_name: str = Field(..., description="User's business name")
    plan: str = Field(..., description="User's plan: 'free' or 'paid'")
    drafts_count: int = Field(..., ge=0, description="Number of drafts created in past 7 days")
    outstanding_amount: Decimal = Field(..., ge=0, description="Total outstanding invoice amount")
    critical_count: int = Field(default=0, ge=0, description="Number of critical/overdue invoices")


class DigestSendRequest(BaseModel):
    """Request schema for sending digest emails (cron endpoint)."""
    secret: str = Field(..., description="Cron secret for authentication")


class DigestSendResponse(BaseModel):
    """Response schema for digest send endpoint."""
    success: bool
    emails_sent: int = Field(..., ge=0, description="Number of digest emails sent")
    emails_failed: int = Field(default=0, ge=0, description="Number of failed email sends")
    message: str

