"""
Cron-triggered API routes.
"""
import logging
import time
from typing import Any
from uuid import uuid4
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.services.system_state import get_system_paused
from app.services.daily_processing import process_user_invoices
from app.services.soak_metrics import record_soak_event

router = APIRouter(prefix="/api/cron", tags=["cron"])
logger = logging.getLogger(__name__)


def _require_cron_secret(x_cron_secret: str | None) -> None:
    if not settings.digest_cron_secret:
        raise HTTPException(status_code=503, detail="Cron secret not configured")
    if not x_cron_secret or x_cron_secret != settings.digest_cron_secret:
        logger.warning("Invalid cron secret provided")
        raise HTTPException(status_code=401, detail="Invalid cron secret")

def _sanitize_attempts(value: int) -> int:
    return max(1, value)


async def _process_user_with_retries(
    user: User,
    db: AsyncSession,
    run_id: str,
) -> tuple[Any | None, int, list[str]]:
    max_attempts = _sanitize_attempts(settings.cron_user_max_attempts)
    delay_seconds = max(0.0, settings.cron_user_retry_delay_seconds)
    attempts = 0
    errors: list[str] = []

    while attempts < max_attempts:
        attempts += 1
        attempt_start = time.monotonic()
        try:
            result = await process_user_invoices(user, db)
            duration_ms = int((time.monotonic() - attempt_start) * 1000)
            record_soak_event(
                {
                    "event": "cron_user_attempt",
                    "run_id": run_id,
                    "user_id": str(user.id),
                    "attempt": attempts,
                    "duration_ms": duration_ms,
                    "errors": bool(result.errors),
                    "drafts_created": result.drafts_created,
                    "invoices_checked": result.invoices_checked,
                    "skipped_reason": result.skipped_reason,
                },
                settings.soak_metrics_path,
            )
            return result, attempts, errors
        except Exception as exc:
            duration_ms = int((time.monotonic() - attempt_start) * 1000)
            error_str = str(exc)
            errors.append(error_str)
            logger.exception(
                "Cron processing error for user %s (attempt %s/%s)",
                user.id,
                attempts,
                max_attempts,
            )
            record_soak_event(
                {
                    "event": "cron_user_attempt_exception",
                    "run_id": run_id,
                    "user_id": str(user.id),
                    "attempt": attempts,
                    "duration_ms": duration_ms,
                    "error": error_str,
                },
                settings.soak_metrics_path,
            )
            if attempts < max_attempts:
                await asyncio.sleep(delay_seconds)

    return None, attempts, errors


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

    run_id = str(uuid4())
    run_start = time.monotonic()

    record_soak_event(
        {
            "event": "cron_run_start",
            "run_id": run_id,
        },
        settings.soak_metrics_path,
    )

    paused = await get_system_paused(db)
    if paused:
        record_soak_event(
            {
                "event": "cron_run_end",
                "run_id": run_id,
                "status": "paused",
                "duration_ms": int((time.monotonic() - run_start) * 1000),
            },
            settings.soak_metrics_path,
        )
        return {
            "success": True,
            "message": "System is paused",
            "users_total": 0,
            "processed": 0,
            "run_id": run_id,
        }

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
    attempts_total = 0
    retries_total = 0

    for user in eligible_users:
        proc_result, attempts, attempt_errors = await _process_user_with_retries(
            user,
            db,
            run_id,
        )
        attempts_total += attempts
        retries_total += max(0, attempts - 1)

        if proc_result is None:
            failed += 1
            errors.append(f"{user.id}: {attempt_errors}")
            continue

        total_drafts += proc_result.drafts_created
        total_invoices += proc_result.invoices_checked
        if proc_result.errors:
            failed += 1
            errors.append(f"{user.id}: {proc_result.errors}")
        else:
            processed += 1

    await db.commit()

    duration_ms = int((time.monotonic() - run_start) * 1000)
    record_soak_event(
        {
            "event": "cron_run_end",
            "run_id": run_id,
            "status": "completed",
            "duration_ms": duration_ms,
            "users_total": len(eligible_users),
            "processed": processed,
            "failed": failed,
            "attempts_total": attempts_total,
            "retries_total": retries_total,
        },
        settings.soak_metrics_path,
    )

    return {
        "success": failed == 0,
        "users_total": len(eligible_users),
        "processed": processed,
        "failed": failed,
        "drafts_created": total_drafts,
        "invoices_checked": total_invoices,
        "errors": errors,
        "attempts_total": attempts_total,
        "retries_total": retries_total,
        "run_id": run_id,
        "duration_ms": duration_ms,
        "soak_metrics_path": settings.soak_metrics_path,
    }
