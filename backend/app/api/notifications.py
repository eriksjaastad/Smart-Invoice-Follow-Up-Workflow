"""
Notification API routes for error notifications.

Provides endpoints for:
- POST /api/notifications/check-failures - Check for consecutive failures and send notifications (cron endpoint)
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.notification import NotificationCheckRequest, NotificationCheckResponse
from app.services.notifications import check_consecutive_failures, send_error_notification

router = APIRouter(prefix="/api/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)


@router.post("/check-failures", response_model=NotificationCheckResponse)
async def check_and_notify_failures(
    request: NotificationCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Check all active users for consecutive failures and send error notifications.
    
    This endpoint is called by a cron job (e.g., Vercel Cron or external scheduler)
    daily to monitor for repeated failures and alert users.
    
    Authentication: Requires DIGEST_CRON_SECRET in request body
    
    Args:
        request: Contains secret for authentication
        db: Database session
        
    Returns:
        NotificationCheckResponse with check results and notification counts
        
    Raises:
        HTTPException 401: If secret is invalid
    """
    # Verify cron secret (reusing DIGEST_CRON_SECRET for simplicity)
    if request.secret != settings.digest_cron_secret:
        logger.warning("Invalid notification cron secret provided")
        raise HTTPException(status_code=401, detail="Invalid cron secret")
    
    # Query all active users
    result = await db.execute(
        select(User).where(User.active == True)
    )
    users = result.scalars().all()
    
    logger.info(f"Checking {len(users)} active users for consecutive failures")
    
    # Check each user for failures
    users_checked = 0
    failures_detected = 0
    notifications_sent = 0
    notifications_failed = 0
    
    for user in users:
        try:
            users_checked += 1
            
            # Check for consecutive failures
            failure_info = await check_consecutive_failures(user.id, db)
            
            if not failure_info:
                # No consecutive failures for this user
                continue
            
            failures_detected += 1
            logger.warning(f"Consecutive failures detected for user {user.id} ({user.email})")
            
            # Send error notification
            success = await send_error_notification(user, failure_info)
            
            if success:
                notifications_sent += 1
                logger.info(f"Error notification sent to {user.email}")
            else:
                notifications_failed += 1
                logger.error(f"Failed to send error notification to {user.email}")
                
        except Exception as e:
            notifications_failed += 1
            logger.error(f"Error processing failure check for user {user.id}: {str(e)}")
    
    # Return summary
    success = notifications_failed == 0
    message = f"Checked {users_checked} users: {failures_detected} failures detected, {notifications_sent} notifications sent, {notifications_failed} failed"
    logger.info(message)
    
    return NotificationCheckResponse(
        success=success,
        users_checked=users_checked,
        failures_detected=failures_detected,
        notifications_sent=notifications_sent,
        notifications_failed=notifications_failed,
        message=message
    )

