"""
Weekly digest email service.

Provides functions for calculating digest data and sending weekly summary emails.
"""
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional
from uuid import UUID

from jinja2 import Template
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import resend

from app.core.config import settings
from app.models.user import User
from app.models.job_history import JobHistory
from app.schemas.digest import DigestData
from app.services.google_workspace import GoogleWorkspaceConfigError, send_delegated_email
from app.services.venture_workflow import record_workflow_event

logger = logging.getLogger(__name__)

# Email template - lazy loaded to prevent startup crash if file is missing
TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "digest_email.html"
_EMAIL_TEMPLATE: Optional[Template] = None


def _get_email_template() -> Template:
    """
    Lazy-load the email template.

    This prevents the app from crashing on startup if the template file is missing.
    Instead, the error will occur only when trying to send a digest email.

    Returns:
        Jinja2 Template object

    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    global _EMAIL_TEMPLATE
    if _EMAIL_TEMPLATE is None:
        try:
            with open(TEMPLATE_PATH, "r") as f:
                _EMAIL_TEMPLATE = Template(f.read())
        except FileNotFoundError:
            logger.error(f"Email template not found at {TEMPLATE_PATH}")
            raise
    return _EMAIL_TEMPLATE


async def calculate_digest(user_id: UUID, db: AsyncSession) -> Optional[DigestData]:
    """
    Calculate weekly digest data for a user.
    
    Queries job_history for the past 7 days and aggregates:
    - Total drafts created
    - Most recent outstanding amount
    - User information for email
    
    Args:
        user_id: UUID of the user
        db: Async database session
        
    Returns:
        DigestData with aggregated information, or None if user not found
    """
    # Fetch user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        logger.warning(f"User {user_id} not found for digest calculation")
        return None
    
    # Calculate date range (past 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # Query job history for past 7 days
    result = await db.execute(
        select(
            func.sum(JobHistory.drafts_created).label('total_drafts'),
            func.max(JobHistory.total_outstanding_amount).label('latest_outstanding')
        )
        .where(JobHistory.user_id == user_id)
        .where(JobHistory.run_at >= seven_days_ago)
    )
    row = result.one_or_none()
    
    # Extract aggregated data
    drafts_count = int(row.total_drafts) if row and row.total_drafts else 0
    outstanding_amount = Decimal(str(row.latest_outstanding)) if row and row.latest_outstanding else Decimal('0.00')
    
    # Create digest data
    digest_data = DigestData(
        user_id=user.id,
        user_name=user.name,
        user_email=user.email,
        business_name=user.business_name,
        plan=user.plan,
        drafts_count=drafts_count,
        outstanding_amount=outstanding_amount,
        critical_count=0  # TODO: Calculate from invoice data when available
    )
    
    return digest_data


async def send_digest_email(digest_data: DigestData) -> bool:
    """
    Send weekly digest email to a user via Resend.
    
    Args:
        digest_data: Digest data for the email
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Check if Resend is configured
        if not settings.resend_api_key or settings.resend_api_key == "you_resend_api_key":
            logger.warning(f"Resend not configured, skipping email to {digest_data.user_email}")
            return False

        # Create email content
        subject = f"Weekly Invoice Summary for {digest_data.business_name}"

        # Render HTML content from template
        template = _get_email_template()
        html_content = template.render(
            user_name=digest_data.user_name,
            business_name=digest_data.business_name,
            drafts_count=digest_data.drafts_count,
            outstanding_amount=digest_data.outstanding_amount,
            critical_count=digest_data.critical_count,
            plan=digest_data.plan,
            frontend_url=settings.frontend_url
        )

        # Send email via Resend
        resend.api_key = settings.resend_api_key
        response = resend.Emails.send({
            "from": settings.resend_from_email,
            "to": [digest_data.user_email],
            "subject": subject,
            "html": html_content
        })

        logger.info(f"Digest email sent successfully to {digest_data.user_email} (id: {response['id']})")
        return True

    except Exception as e:
        logger.error(f"Failed to send digest email to {digest_data.user_email}: {str(e)}")
        return False


def send_daily_ops_digest(summary: dict) -> bool:
    """
    Send the daily ops digest to the internal help desk via delegated Gmail.

    Args:
        summary: Dict with daily processing counts and errors.

    Returns:
        True if email sent successfully, False otherwise.
    """
    recipient = settings.daily_digest_recipient
    if not recipient:
        logger.warning("Daily digest recipient not configured; skipping send")
        record_workflow_event(
            event="daily_digest_send",
            status="skipped",
            details={"reason": "missing_recipient"},
        )
        return False

    date_label = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    subject = f"Daily Smart Invoice Digest ({date_label})"

    html_body = f"""
    <html>
      <body>
        <h2>Daily Processing Summary</h2>
        <ul>
          <li>Users total: {summary.get('users_total', 0)}</li>
          <li>Processed: {summary.get('processed', 0)}</li>
          <li>Failed: {summary.get('failed', 0)}</li>
          <li>Drafts created: {summary.get('drafts_created', 0)}</li>
          <li>Invoices checked: {summary.get('invoices_checked', 0)}</li>
        </ul>
        <p>Errors:</p>
        <pre>{summary.get('errors', [])}</pre>
      </body>
    </html>
    """

    try:
        response = send_delegated_email(
            subject=subject,
            html_body=html_body,
            to_emails=recipient,
            sender=settings.daily_digest_sender or None,
        )
        record_workflow_event(
            event="daily_digest_send",
            status="success",
            details={"recipient": recipient, "message_id": response.get("id")},
        )
        return True
    except GoogleWorkspaceConfigError as exc:
        logger.warning("Daily digest skipped (workspace config): %s", exc)
        record_workflow_event(
            event="daily_digest_send",
            status="skipped",
            details={"reason": "workspace_config", "error": str(exc)},
        )
        return False
    except Exception as exc:
        logger.error("Daily digest send failed: %s", exc)
        record_workflow_event(
            event="daily_digest_send",
            status="failed",
            details={"recipient": recipient, "error": str(exc)},
        )
        return False
