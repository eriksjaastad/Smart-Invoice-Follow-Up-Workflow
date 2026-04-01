"""
Cron-triggered API routes.
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.services.system_state import get_system_paused
from app.services.daily_processing import process_user_invoices
from app.services.digest import send_daily_ops_digest

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
    x_cron_secret: str | None = Header(None),
) -> dict[str, Any]:
    """
    Trigger daily invoice processing for all active users.

    Processes each user's invoices directly via Google APIs.
    Protected by DIGEST_CRON_SECRET via x-cron-secret header.
    """
    _require_cron_secret(x_cron_secret)

    paused = await get_system_paused(db)
    if paused:
        return {"success": True, "message": "System is paused", "users_total": 0, "processed": 0}

    # Get active users with a sheet and valid Google connection
    result = await db.execute(select(User).where(User.active == True))
    all_users = result.scalars().all()
    eligible_users = [
        u for u in all_users
        if u.sheet_id
        and u.google_refresh_token_encrypted
        and not u.google_token_revoked
    ]

    processed = 0
    failed = 0
    total_drafts = 0
    total_invoices = 0
    errors: list[str] = []

    for user in eligible_users:
        try:
            proc_result = await process_user_invoices(user, db)
            total_drafts += proc_result.drafts_created
            total_invoices += proc_result.invoices_checked
            if proc_result.errors:
                failed += 1
                errors.append(f"{user.id}: {proc_result.errors}")
            else:
                processed += 1
        except Exception as e:
            failed += 1
            errors.append(f"{user.id}: {e}")

    await db.commit()

    response_payload = {
        "success": failed == 0,
        "users_total": len(eligible_users),
        "processed": processed,
        "failed": failed,
        "drafts_created": total_drafts,
        "invoices_checked": total_invoices,
        "errors": errors,
    }

    send_daily_ops_digest(response_payload)

    return response_payload
