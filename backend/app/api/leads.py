"""Public lead capture endpoints."""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def capture_lead(payload: LeadCreate, db: AsyncSession = Depends(get_db)):
    """Capture a pre-auth landing-page lead without forcing Auth0."""
    email = payload.email.lower()
    source = payload.source.strip() or "landing"
    intent = payload.intent.strip() if payload.intent else None

    existing = await db.scalar(
        select(Lead).where(Lead.email == email, Lead.source == source)
    )
    if existing:
        existing.intent = intent or existing.intent
        existing.updated_at = datetime.utcnow()
        logger.info("Updated captured lead source=%s", source)
        return LeadResponse(message="You're on the list. We'll send the setup path shortly.")

    db.add(Lead(email=email, source=source, intent=intent))
    logger.info("Captured lead source=%s", source)
    return LeadResponse(message="You're on the list. We'll send the setup path shortly.")
