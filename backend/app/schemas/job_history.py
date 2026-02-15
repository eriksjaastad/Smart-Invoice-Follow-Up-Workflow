"""
Job history Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class JobLogRequest(BaseModel):
    """
    Schema for Make.com webhook payload when posting job results.
    POST /api/webhooks/make-results
    """
    user_id: UUID
    invoices_checked: int = Field(..., ge=0, description="Number of invoices checked")
    drafts_created: int = Field(..., ge=0, description="Number of drafts created")
    total_outstanding_amount: Optional[Decimal] = Field(None, ge=0, description="Total outstanding amount")
    errors: Optional[list[dict[str, Any]]] = Field(None, description="Array of error objects")
    duration_ms: Optional[int] = Field(None, ge=0, description="Execution duration in milliseconds")


class JobHistory(BaseModel):
    """Schema for job history response."""
    id: UUID
    user_id: UUID
    run_at: datetime
    invoices_checked: int
    drafts_created: int
    total_outstanding_amount: Optional[Decimal] = None
    errors: Optional[dict[str, Any]] = None
    duration_ms: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

