"""
Daily invoice processing service.

Replaces the Make.com Daily Processing scenario with direct Google API calls.
For each user: reads their sheet, finds overdue unpaid invoices, determines
escalation stage, creates Gmail drafts, and updates the sheet.
"""
import logging
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_history import JobHistory
from app.models.user import User
from app.services.escalation import days_overdue, stage_for, should_send_draft

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of processing a single user's invoices."""
    user_id: UUID
    invoices_checked: int = 0
    drafts_created: int = 0
    total_outstanding: Decimal = field(default_factory=lambda: Decimal("0"))
    errors: list[dict] = field(default_factory=list)
    duration_ms: int = 0
    skipped_reason: Optional[str] = None


def _parse_date(value: str) -> Optional[date]:
    """Parse a date string from a Google Sheet cell. Tries common formats."""
    if not value or not value.strip():
        return None
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    # Last resort: dateutil
    try:
        from dateutil import parser as dateutil_parser
        return dateutil_parser.parse(value).date()
    except Exception:
        return None


def _parse_amount(value: str) -> Decimal:
    """Parse an amount string, stripping currency symbols."""
    if not value or not value.strip():
        return Decimal("0")
    cleaned = value.strip().replace("$", "").replace(",", "").replace(" ", "")
    try:
        return Decimal(cleaned)
    except Exception:
        return Decimal("0")


def _is_paid(value: str) -> bool:
    """Check if the Paid column indicates payment."""
    return value.strip().upper() in ("TRUE", "YES", "PAID", "1")


def _parse_last_stage(value: str) -> Optional[int]:
    """Parse Last_Stage_Sent column to int."""
    if not value or not value.strip():
        return None
    try:
        return int(value.strip())
    except ValueError:
        return None


async def process_user_invoices(
    user: User,
    db: AsyncSession,
    today: Optional[date] = None,
) -> ProcessingResult:
    """
    Process all overdue invoices for a single user.

    Steps:
    1. Get Google credentials from encrypted refresh token
    2. Read all rows from the user's sheet
    3. Filter to unpaid invoices
    4. For each unpaid row: determine stage, check if draft needed, create draft, update sheet
    5. Record results to job_history

    Args:
        user: User model with sheet_id and google credentials
        db: Async database session
        today: Reference date (defaults to today)

    Returns:
        ProcessingResult with counts and any errors
    """
    if today is None:
        today = date.today()

    # Local imports keep test-only environments from requiring Google modules.
    from app.services.email_templates import get_subject, get_body_html
    from app.services.google_tokens import get_google_credentials
    from app.services.google_sheets import read_invoice_rows, update_row_cells, validate_sheet_columns
    from app.services.google_gmail import create_draft

    start_time = time.time()
    result = ProcessingResult(user_id=user.id)

    # Pre-flight checks
    if not user.sheet_id:
        result.skipped_reason = "no_sheet_id"
        return result

    if not user.google_refresh_token_encrypted:
        result.skipped_reason = "no_google_token"
        return result

    if user.google_token_revoked:
        result.skipped_reason = "token_revoked"
        return result

    # Invoice limit based on plan — free=3 drafts/day, paid=100 drafts/day
    invoice_limit = 3 if user.plan == "free" else 100
    logger.info(
        f"Processing user {user.id}: plan={user.plan}, limit={invoice_limit}, sheet={user.sheet_id}"
    )

    try:
        creds = get_google_credentials(user)
    except ValueError as e:
        result.errors.append({"type": "credentials", "message": str(e)})
        await _record_job(user, result, db)
        return result

    try:
        # Read all rows
        rows = read_invoice_rows(creds, user.sheet_id)
        headers = validate_sheet_columns(creds, user.sheet_id)
    except Exception as e:
        error_str = str(e)
        logger.error(f"Failed to read sheet for user {user.id}: {error_str}")
        # Detect revoked token
        if "401" in error_str or "403" in error_str or "invalid_grant" in error_str:
            user.google_token_revoked = True
            await db.flush()
            result.errors.append({"type": "auth_revoked", "message": error_str})
        else:
            result.errors.append({"type": "sheet_read", "message": error_str})
        await _record_job(user, result, db)
        return result

    # Filter to unpaid invoices
    unpaid_rows = [r for r in rows if not _is_paid(r.get("Paid", ""))]
    result.invoices_checked = len(unpaid_rows)

    # Track outstanding total
    for row in unpaid_rows:
        result.total_outstanding += _parse_amount(row.get("Amount", ""))

    # Process each unpaid invoice (up to limit)
    drafts_this_run = 0
    for row in unpaid_rows:
        if drafts_this_run >= invoice_limit:
            logger.info(
                f"User {user.id}: draft limit reached ({drafts_this_run}/{invoice_limit}), stopping"
            )
            break

        try:
            due_date = _parse_date(row.get("Due_Date", ""))
            if due_date is None:
                continue  # Can't determine overdue status without a date

            overdue_days = days_overdue(due_date, today)
            stage = stage_for(overdue_days)
            if stage is None:
                continue  # Not overdue enough for any reminder

            last_stage = _parse_last_stage(row.get("Last_Stage_Sent", ""))
            last_sent = _parse_date(row.get("Last_Sent_At", ""))

            if not should_send_draft(stage, last_stage, last_sent, today):
                continue

            # Build email
            client_email = row.get("Client_Email", "").strip()
            if not client_email:
                continue

            subject = get_subject(
                stage,
                row.get("Invoice_Number", "N/A"),
                user.business_name,
            )
            body_html = get_body_html(
                stage_days=stage,
                sender_name=user.name,
                business_name=user.business_name,
                client_name=row.get("Client_Name", ""),
                invoice_number=row.get("Invoice_Number", "N/A"),
                amount=row.get("Amount", ""),
                due_date=row.get("Due_Date", ""),
                days_overdue=overdue_days,
            )

            # Create Gmail draft
            create_draft(creds, client_email, subject, body_html)

            # Increment counter IMMEDIATELY after draft creation, BEFORE
            # update_row_cells — if the sheet update throws, the draft was
            # still created and must count toward the limit (#5265).
            drafts_this_run += 1
            result.drafts_created += 1
            logger.info(
                f"Draft {drafts_this_run}/{invoice_limit} created for {row.get('Invoice_Number')}"
            )

            # Defensive safety cap: stop even if we somehow got here
            # with drafts_this_run already at or past the limit.
            if result.drafts_created >= invoice_limit:
                logger.info(
                    f"User {user.id}: safety cap reached ({result.drafts_created}/{invoice_limit}), stopping"
                )
                break

            # Update sheet: Last_Stage_Sent + Last_Sent_At
            update_row_cells(
                creds,
                user.sheet_id,
                row["_row_number"],
                {
                    "Last_Stage_Sent": str(stage),
                    "Last_Sent_At": today.isoformat(),
                },
                headers=headers,
            )

        except Exception as e:
            error_str = str(e)
            logger.warning(
                f"Error processing row {row.get('_row_number')} for user {user.id}: {error_str}"
            )
            # Detect auth revocation mid-processing
            if "401" in error_str or "invalid_grant" in error_str:
                user.google_token_revoked = True
                await db.flush()
                result.errors.append({"type": "auth_revoked", "message": error_str})
                break
            result.errors.append({
                "type": "row_processing",
                "row": row.get("_row_number"),
                "message": error_str,
            })

    result.duration_ms = int((time.time() - start_time) * 1000)

    # Update user's last_run_at
    user.last_run_at = datetime.utcnow()
    await db.flush()

    # Record to job_history
    await _record_job(user, result, db)

    return result


async def _record_job(user: User, result: ProcessingResult, db: AsyncSession) -> None:
    """Record processing result in job_history table."""
    job = JobHistory(
        user_id=user.id,
        invoices_checked=result.invoices_checked,
        drafts_created=result.drafts_created,
        total_outstanding_amount=float(result.total_outstanding) if result.total_outstanding else None,
        errors=result.errors if result.errors else None,
        duration_ms=result.duration_ms,
    )
    db.add(job)
    await db.flush()
