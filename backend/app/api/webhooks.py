"""
Webhook API routes for external integrations.

Provides endpoints for:
- POST /api/webhooks/make-results - Receive job results from Make.com scenarios
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, date

from app.core.auth import verify_make_api_key
from app.db.session import get_db
from app.models.user import User
from app.models.job_history import JobHistory
from app.schemas.webhook import MakeWebhookRequest, MakeWebhookResponse

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/make-results", response_model=MakeWebhookResponse)
async def receive_make_results(
    payload: MakeWebhookRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_make_api_key)
):
    """
    Receive job results from Make.com scenarios.

    Make.com scenarios POST results after processing invoices:
    - user_id: UUID of the user
    - drafts_created: Number of Gmail drafts created
    - invoices_checked: Number of invoices processed
    - total_outstanding_amount: Sum of all unpaid invoice amounts
    - errors: Optional list of error messages
    - duration_ms: Optional execution time in milliseconds

    This endpoint:
    1. Validates the user exists and is active
    2. Checks for existing job_history record for today (idempotency)
    3. Updates existing record or creates new one
    4. Updates the user's last_run_at timestamp

    Authentication: Requires MAKE_WEBHOOK_API_KEY in Authorization header

    Args:
        payload: Webhook payload from Make.com
        db: Database session

    Returns:
        Success confirmation with job_id

    Raises:
        HTTPException 400: If data is invalid
        HTTPException 404: If user not found or inactive
        HTTPException 401: If API key is invalid
    """
    # Validate user exists and is active
    result = await db.execute(
        select(User).where(User.id == payload.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.active:
        raise HTTPException(status_code=404, detail="User is inactive")

    # Check for existing record for this user today (idempotency)
    today = date.today()
    stmt = select(JobHistory).where(
        JobHistory.user_id == payload.user_id,
        func.date(JobHistory.run_at) == today
    )
    existing_result = await db.execute(stmt)
    existing_record = existing_result.scalar_one_or_none()

    if existing_record:
        # Update existing record
        existing_record.drafts_created = payload.drafts_created
        existing_record.total_outstanding_amount = payload.total_outstanding_amount
        existing_record.run_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(f"Updated existing job_history record for user {payload.user_id}")
        job_id = existing_record.id
    else:
        # Create new record
        job = JobHistory(
            user_id=payload.user_id,
            run_at=datetime.now(timezone.utc),
            invoices_checked=payload.invoices_checked,
            drafts_created=payload.drafts_created,
            total_outstanding_amount=payload.total_outstanding_amount,
            errors=payload.errors or [],
            duration_ms=payload.duration_ms
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        logger.info(f"Created new job_history record for user {payload.user_id}")
        job_id = job.id

    # Update user's last_run_at timestamp
    user.last_run_at = datetime.now(timezone.utc)
    await db.commit()

    return MakeWebhookResponse(
        success=True,
        job_id=job_id,
        message=f"Job logged successfully. Processed {payload.invoices_checked} invoices, created {payload.drafts_created} drafts."
    )

