"""
Weekly digest email service.

Provides functions for calculating digest data and sending weekly summary emails.
"""
import logging
from datetime import datetime, timedelta
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

