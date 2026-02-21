"""
Onboarding flow API routes.

Provides endpoints for the onboarding process:
1. Select or create Google Sheet (via Make.com webhooks)
2. Provide sender information
3. Activate account

Note: Google OAuth and Sheets API interactions are handled by Make.com webhooks.
Users share their Google Sheet directly - no OAuth dance needed.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
import httpx

from app.core.auth import require_auth
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])

# Required columns for invoice sheet validation
REQUIRED_COLUMNS = [
    "Invoice_Number",
    "Client_Name",
    "Client_Email",
    "Amount",
    "Due_Date",
    "Sent_Date",
    "Paid"
]

# Request/Response models for onboarding steps


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


@router.get("/connect-google")
async def connect_google(
    current_user: User = Depends(require_auth)
):
    """
    Step 1: Redirect user to Make.com for Google OAuth connection.

    This initiates the Make.com connection flow where users authorize:
    - gmail.compose
    - spreadsheets

    Note: The specific URL is managed in Make.com.
    """
    # Use the first sheet list webhook as a proxy or a specific OAuth start URL if available
    # For MVP, we redirect to a Make.com scenario that handles connection
    if not settings.make_list_sheets_webhook_url:
        raise HTTPException(
            status_code=503,
            detail="Service not configured. Make.com webhook URL is missing."
        )
    
    # We redirect them to the Make.com webhook which will then redirect to Google
    # Or in many Make.com setups, we just provide the link to their scenario/connection page
    return {"url": settings.make_list_sheets_webhook_url}
async def list_sheets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Step 1: List user's Google Sheets via Make.com webhook.

    Calls Make.com webhook to retrieve the user's Google Sheets.
    Users share their sheet directly - no OAuth dance needed.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        List of user's Google Sheets

    Raises:
        HTTPException 503: If webhook URL is not configured
        HTTPException 500: If webhook call fails
    """
    # Check if webhook URL is configured
    if not settings.make_list_sheets_webhook_url:
        raise HTTPException(
            status_code=503,
            detail="Service not configured. Make.com list sheets webhook URL is missing."
        )

    try:
        # Call Make.com webhook to list sheets
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                settings.make_list_sheets_webhook_url,
                json={"user_id": str(current_user.id)}
            )
            response.raise_for_status()

            # Parse response from Make.com
            data = response.json()
            return SheetsListResponse(sheets=data.get("sheets", []))

    except httpx.TimeoutException:
        logger.error(f"Timeout calling Make.com list sheets webhook for user {current_user.id}")
        raise HTTPException(
            status_code=500,
            detail="Request to list sheets timed out. Please try again."
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from Make.com list sheets webhook: {e.response.status_code}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list sheets: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Error calling Make.com list sheets webhook: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list sheets. Please try again."
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

    Optional columns (can be added if missing):
    - Last_Stage_Sent
    - Last_Sent_At

    Calls Make.com webhook to read sheet headers and validate against required columns.

    Args:
        request: Sheet ID to validate
        db: Database session
        current_user: Authenticated user

    Returns:
        Validation result with missing columns

    Raises:
        HTTPException 503: If webhook URL is not configured
        HTTPException 500: If webhook call fails
    """
    # Check if webhook URL is configured
    if not settings.make_validate_sheet_webhook_url:
        raise HTTPException(
            status_code=503,
            detail="Service not configured. Make.com validate sheet webhook URL is missing."
        )

    try:
        # Call Make.com webhook to read sheet headers
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                settings.make_validate_sheet_webhook_url,
                json={"sheet_id": request.sheet_id}
            )
            response.raise_for_status()

            # Parse response from Make.com
            data = response.json()
            columns = data.get("columns", [])

            # Check for missing required columns
            missing_columns = [col for col in REQUIRED_COLUMNS if col not in columns]

            return SheetValidationResponse(
                valid=len(missing_columns) == 0,
                missing_columns=missing_columns
            )

    except httpx.TimeoutException:
        logger.error(f"Timeout calling Make.com validate sheet webhook for sheet {request.sheet_id}")
        raise HTTPException(
            status_code=500,
            detail="Request to validate sheet timed out. Please try again."
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from Make.com validate sheet webhook: {e.response.status_code}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate sheet: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Error calling Make.com validate sheet webhook: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to validate sheet. Please try again."
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

    Creates a new sheet with all required columns pre-populated via Make.com webhook.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        New sheet ID and URL

    Raises:
        HTTPException 503: If webhook URL is not configured
        HTTPException 500: If webhook call fails
    """
    # Check if webhook URL is configured
    if not settings.make_create_template_webhook_url:
        raise HTTPException(
            status_code=503,
            detail="Service not configured. Make.com create template webhook URL is missing."
        )

    try:
        # Call Make.com webhook to create template sheet
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                settings.make_create_template_webhook_url,
                json={"user_id": str(current_user.id)}
            )
            response.raise_for_status()

            # Parse response from Make.com
            data = response.json()
            return CreateTemplateResponse(
                sheet_id=data["sheet_id"],
                sheet_url=data["sheet_url"]
            )

    except httpx.TimeoutException:
        logger.error(f"Timeout calling Make.com create template webhook for user {current_user.id}")
        raise HTTPException(
            status_code=500,
            detail="Request to create template sheet timed out. Please try again."
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from Make.com create template webhook: {e.response.status_code}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create template sheet: {e.response.text}"
        )
    except KeyError as e:
        logger.error(f"Missing expected field in Make.com response: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Invalid response from template creation service."
        )
    except Exception as e:
        logger.error(f"Error calling Make.com create template webhook: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create template sheet. Please try again."
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

