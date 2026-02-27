"""
Cron-triggered API routes.
"""
import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.services.system_state import get_system_paused

router = APIRouter(prefix="/api/cron", tags=["cron"])
logger = logging.getLogger(__name__)


def _require_cron_secret(x_cron_secret: str | None) -> None:
    if not settings.digest_cron_secret:
        raise HTTPException(status_code=503, detail="Cron secret not configured")
    if not x_cron_secret or x_cron_secret != settings.digest_cron_secret:
        logger.warning("Invalid cron secret provided")
        raise HTTPException(status_code=401, detail="Invalid cron secret")


@router.post("/trigger-daily")
async def trigger_daily_processing(
    db: AsyncSession = Depends(get_db),
    x_cron_secret: str | None = Header(None)
) -> dict[str, Any]:
    """
    Trigger Make.com Daily Processing for all active users.

    Protected by DIGEST_CRON_SECRET via x-cron-secret header.
    """
    _require_cron_secret(x_cron_secret)

    if not settings.make_daily_processing_webhook_url:
        raise HTTPException(status_code=503, detail="Make.com Daily Processing webhook URL missing")
    if not settings.backend_url:
        raise HTTPException(status_code=503, detail="BACKEND_URL not configured")

    backend_url = settings.backend_url.rstrip("/")
    paused = await get_system_paused(db)

    result = await db.execute(select(User).where(User.active == True))
    users = result.scalars().all()

    sent = 0
    failed = 0
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=30) as client:
        for user in users:
            invoice_limit = 3 if user.plan == "free" else 100
            payload = {
                "user_id": str(user.id),
                "email": user.email,
                "sender_name": user.name,
                "business_name": user.business_name,
                "sheet_id": user.sheet_id,
                "active": user.active,
                "paused": paused,
                "backend_url": backend_url,
                "plan": user.plan,
                "invoice_limit": invoice_limit,
            }
            try:
                response = await client.post(
                    settings.make_daily_processing_webhook_url,
                    json=payload,
                )
                response.raise_for_status()
                sent += 1
            except Exception as e:
                failed += 1
                errors.append(f"{user.id}: {e}")

    return {
        "success": failed == 0,
        "users_total": len(users),
        "sent": sent,
        "failed": failed,
        "errors": errors,
    }
