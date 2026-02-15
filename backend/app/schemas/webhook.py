"""
Webhook Pydantic schemas for Make.com integration.
"""
from typing import Any, Optional
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field


class MakeWebhookRequest(BaseModel):
    """
    Schema for Make.com webhook requests.
    This is the payload Make.com sends to POST /api/webhooks/make-results
    """
    user_id: UUID = Field(..., description="User ID from Make.com build variable")
    invoices_checked: int = Field(..., ge=0, description="Number of invoices checked")
    drafts_created: int = Field(..., ge=0, description="Number of Gmail drafts created")
    total_outstanding_amount: Optional[Decimal] = Field(None, ge=0, description="Total outstanding amount")
    errors: Optional[list[dict[str, Any]]] = Field(default=None, description="Array of error objects")
    duration_ms: Optional[int] = Field(None, ge=0, description="Scenario execution duration in ms")


class MakeWebhookResponse(BaseModel):
    """Response schema for webhook endpoints."""
    success: bool
    message: str
    job_id: Optional[UUID] = None

