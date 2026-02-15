"""
Digest API routes for weekly email summaries.

Provides endpoints for:
- POST /api/digest/send - Send weekly digest emails to all active users (cron endpoint)
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.digest import DigestSendRequest, DigestSendResponse
from app.services.digest import calculate_digest, send_digest_email

router = APIRouter(prefix="/api/digest", tags=["digest"])
logger = logging.getLogger(__name__)


@router.post("/send", response_model=DigestSendResponse)
async def send_weekly_digests(
    request: DigestSendRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send weekly digest emails to all active users.
    
    This endpoint is called by a cron job (e.g., Vercel Cron or external scheduler)
    every Monday morning to send weekly summaries.
    
    Authentication: Requires DIGEST_CRON_SECRET in request body
    
    Args:
        request: Contains secret for authentication
        db: Database session
        
    Returns:
        DigestSendResponse with success status and email counts
        
    Raises:
        HTTPException 401: If secret is invalid
    """
    # Verify cron secret
    if request.secret != settings.digest_cron_secret:
        logger.warning("Invalid digest cron secret provided")
        raise HTTPException(status_code=401, detail="Invalid cron secret")
    
    # Query all active users
    result = await db.execute(
        select(User).where(User.active == True)
    )
    users = result.scalars().all()
    
    logger.info(f"Starting weekly digest send for {len(users)} active users")
    
    # Send digest to each user
    emails_sent = 0
    emails_failed = 0
    
    for user in users:
        try:
            # Calculate digest data
            digest_data = await calculate_digest(user.id, db)
            
            if not digest_data:
                logger.warning(f"Could not calculate digest for user {user.id}")
                emails_failed += 1
                continue
            
            # Skip users with no activity (0 drafts)
            if digest_data.drafts_count == 0:
                logger.debug(f"Skipping user {user.id} - no drafts this week")
                continue
            
            # Send email
            success = await send_digest_email(digest_data)
            
            if success:
                emails_sent += 1
                logger.info(f"Digest sent successfully to {user.email}")
            else:
                emails_failed += 1
                logger.error(f"Failed to send digest to {user.email}")
                
        except Exception as e:
            emails_failed += 1
            logger.error(f"Error processing digest for user {user.id}: {str(e)}")
    
    # Return summary
    total_processed = emails_sent + emails_failed
    success = emails_failed == 0
    
    message = f"Processed {total_processed} users: {emails_sent} sent, {emails_failed} failed"
    logger.info(message)
    
    return DigestSendResponse(
        success=success,
        emails_sent=emails_sent,
        emails_failed=emails_failed,
        message=message
    )

