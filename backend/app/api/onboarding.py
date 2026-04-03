"""
Onboarding flow API routes.

Provides endpoints for the onboarding process:
1. Connect Google account (OAuth flow via /api/auth/google/connect)
2. Paste Google Sheet URL or create a new template sheet
3. Provide sender information and activate account
"""
import logging
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List

from app.core.auth import require_auth
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema
from app.services.google_tokens import get_google_credentials
from app.services import google_sheets

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
    "Paid",
]


# Request/Response models

class SheetValidationRequest(BaseModel):
    sheet_id: str = Field(..., description="Google Sheet ID to validate")


class SheetValidationResponse(BaseModel):
    valid: bool = Field(..., description="Whether sheet has all required columns")
    missing_columns: List[str] = Field(default_factory=list)


class SelectSheetRequest(BaseModel):
    sheet_id: str = Field(..., description="Google Sheet ID to use")


class CreateTemplateResponse(BaseModel):
    sheet_id: str = Field(..., description="ID of newly created sheet")
    sheet_url: str = Field(..., description="URL to open the sheet")


class SenderInfoRequest(BaseModel):
    name: str = Field(..., min_length=1, description="User's full name")
    business_name: str = Field(..., min_length=1, description="Business name")


def _require_google_connected(user: User) -> None:
    """Raise 400 if user hasn't connected their Google account."""
    if not user.google_refresh_token_encrypted or user.google_token_revoked:
        raise HTTPException(
            status_code=400,
            detail="Google account not connected. Please connect your Google account first.",
        )


@router.post("/validate-sheet", response_model=SheetValidationResponse)
async def validate_sheet(
    request: SheetValidationRequest,
    current_user: User = Depends(require_auth),
):
    """
    Validate that a sheet has all required columns.

    Reads row 1 headers from the sheet and checks against required columns.
    """
    _require_google_connected(current_user)

    try:
        creds = get_google_credentials(current_user)
        columns = google_sheets.validate_sheet_columns(creds, request.sheet_id)
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in columns]
        return SheetValidationResponse(
            valid=len(missing_columns) == 0,
            missing_columns=missing_columns,
        )
    except Exception as e:
        logger.error(f"Failed to validate sheet {request.sheet_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate sheet. Please try again.")


@router.post("/select-sheet", response_model=UserSchema)
async def select_sheet(
    request: SelectSheetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """
    Select a sheet to use for invoice tracking. Stores sheet_id on user record.

    Accepts either a full Google Sheets URL or a bare sheet ID.
    """
    raw = request.sheet_id.strip().rstrip("/")
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", raw)
    sheet_id = match.group(1) if match else raw

    current_user.sheet_id = sheet_id
    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.post("/create-template", response_model=CreateTemplateResponse)
async def create_template(current_user: User = Depends(require_auth)):
    """
    Create a new Google Sheet with the Invoice Tracker template headers.

    Uses the user's connected Google account to create the sheet in their Drive.
    """
    _require_google_connected(current_user)

    try:
        creds = get_google_credentials(current_user)
        result = google_sheets.create_template_sheet(creds)
        return CreateTemplateResponse(sheet_id=result["sheet_id"], sheet_url=result["sheet_url"])
    except Exception as e:
        logger.error(f"Failed to create template for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create template sheet. Please try again."
        )


@router.post("/sender-info", response_model=UserSchema)
async def submit_sender_info(
    request: SenderInfoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """
    Final onboarding step. Stores sender info and activates account.
    """
    current_user.name = request.name
    current_user.business_name = request.business_name
    current_user.active = True

    await db.commit()
    await db.refresh(current_user)

    return current_user
