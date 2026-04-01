"""
User management API routes.

Provides endpoints for:
- GET /api/users/{user_id}/config - Fetch user config for Make.com scenarios
- PATCH /api/users/{user_id} - Update user profile
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID

from app.core.config import settings
from app.core.auth import require_auth, verify_make_api_key
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema, UserUpdate, UserConfig
from app.services.system_state import get_system_paused

router = APIRouter(prefix="/api/users", tags=["users"])

def get_missing_onboarding_fields(user: User) -> list[str]:
    missing: list[str] = []
    if not user.sheet_id:
        missing.append("sheet_id")
    if not user.name or not user.business_name:
        missing.append("sender_info")
    return missing


@router.get("/{user_id}/config", response_model=UserConfig)
async def get_user_config(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_make_api_key)
):
    """
    Get user configuration for Make.com scenarios.
    
    This endpoint is called by Make.com scenarios at runtime to fetch:
    - sheet_id: Google Sheet ID to process
    - sender_name: User's name for email signatures
    - business_name: Business name for email content
    - plan: "free" or "paid"
    - invoice_limit: 3 for free tier, 100 for paid tier
    
    Authentication: Requires MAKE_WEBHOOK_API_KEY in Authorization header
    
    Args:
        user_id: UUID of the user
        db: Database session
        
    Returns:
        UserConfig with sheet_id, sender_name, business_name, plan, invoice_limit
        
    Raises:
        HTTPException 404: If user not found or inactive
        HTTPException 401: If API key is invalid
    """
    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    # Return 404 if user not found or inactive
    if not user or not user.active:
        raise HTTPException(status_code=404, detail="User not found or inactive")

    missing_fields = get_missing_onboarding_fields(user)
    if missing_fields:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "User onboarding is incomplete. Required inputs are missing.",
                "missing_fields": missing_fields,
                "recovery": {
                    "next_step": "complete_onboarding",
                    "action_url": "/onboarding.html?resume=1",
                    "steps": [
                        "Connect your Google account if prompted.",
                        "Provide a Google Sheet ID.",
                        "Confirm sender name and business name."
                    ]
                }
            }
        )
    
    # Calculate invoice_limit based on plan
    invoice_limit = 3 if user.plan == "free" else 100
    paused = await get_system_paused(db)
    backend_url = settings.backend_url.rstrip("/") if settings.backend_url else ""
    
    # Return config
    return UserConfig(
        user_id=user.id,
        email=user.email,
        sender_name=user.name,
        business_name=user.business_name,
        sheet_id=user.sheet_id,
        active=user.active,
        paused=paused,
        backend_url=backend_url,
        plan=user.plan,
        invoice_limit=invoice_limit
    )


@router.patch("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Update user profile.
    
    Users can only update their own profile.
    
    Args:
        user_id: UUID of the user to update
        user_update: Fields to update
        db: Database session
        current_user: Authenticated user from JWT
        
    Returns:
        Updated user object
        
    Raises:
        HTTPException 403: If user tries to update another user's profile
        HTTPException 404: If user not found
    """
    # Ensure user can only update their own profile
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Cannot update another user's profile")
    
    # Fetch user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return user
