"""
Onboarding flow API routes.

Provides endpoints for the 4-step onboarding process:
1. Connect Google account via Make.com OAuth
2. Select or create Google Sheet
3. Provide sender information
4. Activate account

Note: Google OAuth and Sheets API interactions are handled by Make.com,
not directly by this backend. We provide endpoints that coordinate with Make.com.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

from app.core.auth import require_auth
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


# Request/Response models for onboarding steps

class ConnectGoogleRequest(BaseModel):
    """Request to initiate Google OAuth via Make.com"""
    pass  # No fields needed - user is from JWT


class ConnectGoogleResponse(BaseModel):
    """Response with Make.com OAuth URL"""
    oauth_url: str = Field(..., description="URL to redirect user to for Google OAuth")
    state: str = Field(..., description="CSRF protection state parameter")


class GoogleCallbackRequest(BaseModel):
    """Callback from Make.com after Google OAuth"""
    state: str = Field(..., description="CSRF state parameter to verify")
    scenario_id: str = Field(..., description="Make.com scenario ID for this user")


class SheetInfo(BaseModel):
    """Google Sheet information"""
    id: str = Field(..., description="Google Sheet ID")
    name: str = Field(..., description="Sheet name/title")


class SheetsListResponse(BaseModel):
    """List of user's Google Sheets"""
    sheets: List[SheetInfo]


class SheetValidationRequest(BaseModel):
    """Request to validate a sheet"""
    sheet_id: str = Field(..., description="Google Sheet ID to validate")


class SheetValidationResponse(BaseModel):
    """Sheet validation result"""
    valid: bool = Field(..., description="Whether sheet has all required columns")
    missing_columns: List[str] = Field(default_factory=list, description="List of missing column names")


class SelectSheetRequest(BaseModel):
    """Request to select a sheet"""
    sheet_id: str = Field(..., description="Google Sheet ID to use")


class CreateTemplateResponse(BaseModel):
    """Response after creating template sheet"""
    sheet_id: str = Field(..., description="ID of newly created sheet")
    sheet_url: str = Field(..., description="URL to open the sheet")


class SenderInfoRequest(BaseModel):
    """Sender information for email signatures"""
    name: str = Field(..., min_length=1, description="User's full name")
    business_name: str = Field(..., min_length=1, description="Business name")


# Onboarding endpoints

@router.post("/connect-google", response_model=ConnectGoogleResponse)
async def connect_google(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Step 1: Initiate Google OAuth via Make.com.
    
    TODO: This endpoint needs to:
    1. Generate a CSRF state parameter
    2. Store state in session or database
    3. Call Make.com API to get OAuth URL
    4. Return OAuth URL to frontend
    
    For now, this is a placeholder that returns a mock URL.
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        OAuth URL and state parameter
    """
    # TODO: Implement Make.com OAuth URL generation
    # This requires Make.com API integration
    raise HTTPException(
        status_code=501,
        detail="Google OAuth integration not yet implemented. Requires Make.com API setup."
    )


@router.get("/callback", response_model=UserSchema)
async def google_callback(
    state: str,
    scenario_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Step 1 (callback): Handle OAuth callback from Make.com.
    
    After user authorizes Google access, Make.com calls this endpoint
    with the scenario_id that was created for this user.
    
    Args:
        state: CSRF state parameter to verify
        scenario_id: Make.com scenario ID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Updated user object with scenario_id stored
    """
    # TODO: Verify state parameter matches what we stored
    
    # Store scenario_id in user record
    current_user.make_scenario_id = scenario_id
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.get("/sheets", response_model=SheetsListResponse)
async def list_sheets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Step 2: List user's Google Sheets via Make.com.

    TODO: This endpoint needs to call Make.com API to list sheets.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        List of user's Google Sheets
    """
    # TODO: Call Make.com API to list user's sheets
    raise HTTPException(
        status_code=501,
        detail="Sheet listing not yet implemented. Requires Make.com API integration."
    )


@router.post("/validate-sheet", response_model=SheetValidationResponse)
async def validate_sheet(
    request: SheetValidationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Step 2: Validate that a sheet has all required columns.

    Required columns:
    - Invoice_Number
    - Client_Name
    - Client_Email
    - Amount
    - Due_Date
    - Sent_Date
    - Paid
    - Last_Stage_Sent (optional, will be added if missing)
    - Last_Sent_At (optional, will be added if missing)

    TODO: This endpoint needs to call Make.com API to read sheet headers.

    Args:
        request: Sheet ID to validate
        db: Database session
        current_user: Authenticated user

    Returns:
        Validation result with missing columns
    """
    # TODO: Call Make.com API to read sheet headers and validate
    raise HTTPException(
        status_code=501,
        detail="Sheet validation not yet implemented. Requires Make.com API integration."
    )


@router.post("/select-sheet", response_model=UserSchema)
async def select_sheet(
    request: SelectSheetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Step 2: Select a validated sheet to use.

    This endpoint:
    1. Validates the sheet has required columns (via Make.com API)
    2. Stores sheet_id in user record if valid
    3. Returns error if sheet is invalid

    Args:
        request: Sheet ID to select
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated user object with sheet_id stored

    Raises:
        HTTPException 400: If sheet is invalid (missing required columns)
    """
    # TODO: Validate sheet via Make.com API
    # For now, just store the sheet_id

    current_user.sheet_id = request.sheet_id
    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.post("/create-template", response_model=CreateTemplateResponse)
async def create_template_sheet(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Step 2 (alternative): Create a new Google Sheet with template columns.

    Creates a new sheet with all required columns pre-populated.

    TODO: This endpoint needs to call Make.com API to create sheet.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        New sheet ID and URL
    """
    # TODO: Call Make.com API to create template sheet
    raise HTTPException(
        status_code=501,
        detail="Template creation not yet implemented. Requires Make.com API integration."
    )


@router.post("/sender-info", response_model=UserSchema)
async def submit_sender_info(
    request: SenderInfoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Step 3: Submit sender information (name and business name).

    This is the final step of onboarding. After this:
    - User's name and business_name are stored
    - User is marked as active=true
    - User can start using the service

    Args:
        request: Sender information
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated user object with sender info and active=true
    """
    # Update user with sender info
    current_user.name = request.name
    current_user.business_name = request.business_name
    current_user.active = True

    await db.commit()
    await db.refresh(current_user)

    return current_user

