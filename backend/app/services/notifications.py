"""
Error notification service.

Provides functions for tracking consecutive failures and sending error notification emails.
"""
import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
import resend
from jinja2 import Template
from pathlib import Path

from app.core.config import settings
from app.models.user import User
from app.models.job_history import JobHistory

logger = logging.getLogger(__name__)


async def check_consecutive_failures(user_id: UUID, db: AsyncSession) -> Optional[dict]:
    """
    Check if a user has 3 consecutive job failures.
    
    Args:
        user_id: UUID of the user
        db: Async database session
        
    Returns:
        Dict with failure info if 3 consecutive failures detected, None otherwise
        {
            'user_id': UUID,
            'failure_count': int,
            'last_error': dict,
            'error_type': str  # 'sheet_access', 'make_connection', 'generic'
        }
    """
    # Query last 3 job history records for this user
    result = await db.execute(
        select(JobHistory)
        .where(JobHistory.user_id == user_id)
        .order_by(desc(JobHistory.run_at))
        .limit(3)
    )
    recent_jobs = result.scalars().all()
    
    # Need at least 3 jobs to check for consecutive failures
    if len(recent_jobs) < 3:
        return None
    
    # Check if all 3 have errors
    all_failed = all(job.errors is not None and len(job.errors) > 0 for job in recent_jobs)
    
    if not all_failed:
        return None
    
    # Determine error type from most recent error
    last_error = recent_jobs[0].errors
    error_type = classify_error(last_error)
    
    return {
        'user_id': user_id,
        'failure_count': 3,
        'last_error': last_error,
        'error_type': error_type
    }


def classify_error(error_data: dict) -> str:
    """
    Classify error type based on error data.
    
    Args:
        error_data: Error dict from job_history.errors
        
    Returns:
        Error type: 'sheet_access', 'make_connection', or 'generic'
    """
    if not error_data:
        return 'generic'
    
    # Convert to string for pattern matching
    error_str = str(error_data).lower()
    
    # Check for sheet access errors
    if any(keyword in error_str for keyword in ['permission', 'access denied', 'forbidden', '403', 'sheet']):
        return 'sheet_access'
    
    # Check for Google OAuth/token errors
    if any(keyword in error_str for keyword in [
        'oauth', 'token', 'expired', 'unauthorized', '401',
        'invalid_grant', 'auth_revoked', 'revoked',
    ]):
        return 'google_connection'
    
    return 'generic'


async def send_error_notification(user: User, failure_info: dict) -> bool:
    """
    Send error notification email to a user.
    
    Args:
        user: User model instance
        failure_info: Dict with failure information from check_consecutive_failures
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Check if Resend is configured
        if not settings.resend_api_key or settings.resend_api_key == "you_resend_api_key":
            logger.warning(f"Resend not configured, skipping error notification to {user.email}")
            return False

        # Load appropriate template based on error type
        error_type = failure_info['error_type']
        template_path = Path(__file__).parent.parent / "templates" / f"error_{error_type}.html"

        # Fall back to generic template if specific template doesn't exist
        if not template_path.exists():
            template_path = Path(__file__).parent.parent / "templates" / "error_generic.html"

        with open(template_path, "r") as f:
            template = Template(f.read())

        # Render email content
        html_content = template.render(
            user_name=user.name,
            business_name=user.business_name,
            error_type=error_type,
            error_details=failure_info['last_error'],
            frontend_url=settings.frontend_url
        )

        # Create subject based on error type
        subject_map = {
            'sheet_access': f"Action Required: Google Sheets Access Lost - {user.business_name}",
            'google_connection': f"Action Required: Reconnect Your Google Account - {user.business_name}",
            'generic': f"Action Required: Invoice Collection Errors - {user.business_name}",
        }
        subject = subject_map.get(error_type, subject_map['generic'])

        # Send email via Resend
        resend.api_key = settings.resend_api_key
        response = resend.Emails.send({
            "from": settings.resend_from_email,
            "to": [user.email],
            "subject": subject,
            "html": html_content
        })

        logger.info(f"Error notification sent successfully to {user.email} (type: {error_type}, id: {response['id']})")
        return True

    except Exception as e:
        logger.error(f"Failed to send error notification to {user.email}: {str(e)}")
        return False

