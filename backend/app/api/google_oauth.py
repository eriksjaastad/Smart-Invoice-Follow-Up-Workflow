"""
Google OAuth flow endpoints.

Handles the connect/callback/disconnect flow for users to authorize
their Google account (Sheets + Gmail) with our application.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from sqlalchemy.ext.asyncio import AsyncSession
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.core.auth import require_auth
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.services.google_tokens import encrypt_token, get_google_credentials, GOOGLE_SCOPES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/google", tags=["google-oauth"])

# State signer — uses the app's secret_key (already used for sessions)
_signer = URLSafeTimedSerializer(settings.secret_key)


def _build_flow(state: str | None = None) -> Flow:
    """Build a Google OAuth flow from config."""
    client_config = {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_redirect_uri],
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=GOOGLE_SCOPES,
        state=state,
    )
    flow.redirect_uri = settings.google_redirect_uri
    return flow


@router.get("/connect")
async def connect_google(current_user: User = Depends(require_auth)):
    """
    Start Google OAuth flow. Returns the authorization URL.

    The frontend should redirect the user to this URL.
    """
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    # Build flow first to capture the code_verifier it generates
    flow = _build_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",  # Forces refresh token even if previously authorized
        include_granted_scopes="true",
    )

    # Sign the user ID + code_verifier into the state param so they survive the redirect
    import json
    state_data = json.dumps({
        "user_id": str(current_user.id),
        "code_verifier": flow.code_verifier,
    })
    signed_state = _signer.dumps(state_data)

    # Replace the state in the auth URL with our signed version
    from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
    parsed = urlparse(auth_url)
    params = parse_qs(parsed.query)
    params["state"] = [signed_state]
    new_query = urlencode({k: v[0] for k, v in params.items()})
    auth_url = urlunparse(parsed._replace(query=new_query))

    return {"url": auth_url}


@router.get("/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Google OAuth callback. Exchanges code for tokens and stores encrypted refresh token.

    Google redirects here after user authorizes (or denies).
    """
    frontend_url = settings.frontend_url.rstrip("/")

    # Handle user denial
    if error:
        logger.warning(f"Google OAuth denied: {error}")
        return RedirectResponse(f"{frontend_url}/onboarding.html?google=denied&error={error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")

    # Recover user ID and code_verifier from signed state
    try:
        state_raw = _signer.loads(state, max_age=600)  # 10-minute expiry
    except SignatureExpired:
        return RedirectResponse(f"{frontend_url}/onboarding.html?google=expired")
    except BadSignature:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    import json
    try:
        state_data = json.loads(state_raw)
        user_id_str = state_data["user_id"]
        code_verifier = state_data.get("code_verifier")
    except (json.JSONDecodeError, KeyError):
        # Backwards compat: old state format was just the user_id string
        user_id_str = state_raw
        code_verifier = None

    # Exchange code for tokens
    flow = _build_flow(state=state)
    if code_verifier:
        flow.code_verifier = code_verifier
    try:
        flow.fetch_token(code=code)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Google token exchange failed: {type(e).__name__}: {e}\n{tb}")
        err_type = type(e).__name__
        return RedirectResponse(
            f"{frontend_url}/onboarding.html?google=error&detail=token_exchange_failed&error_type={err_type}&error_msg={str(e)[:200]}"
        )

    credentials = flow.credentials
    if not credentials.refresh_token:
        logger.error("No refresh token received from Google")
        return RedirectResponse(f"{frontend_url}/onboarding.html?google=error&detail=no_refresh_token")

    # Get the user's Google email from ID token info
    try:
        google_email = None
        if hasattr(credentials, "id_token") and credentials.id_token:
            google_email = credentials.id_token.get("email")

        # If we didn't get email from ID token, fetch it from userinfo
        if not google_email:
            from googleapiclient.discovery import build

            oauth2_service = build("oauth2", "v2", credentials=credentials, cache_discovery=False)
            user_info = oauth2_service.userinfo().get().execute()
            google_email = user_info.get("email")
    except Exception as e:
        logger.error(f"Failed to get Google email: {type(e).__name__}: {e}")
        google_email = None  # Continue without email — not fatal

    # Look up user and store encrypted refresh token
    try:
        from sqlalchemy import select

        result = await db.execute(select(User).where(User.id == user_id_str))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.google_refresh_token_encrypted = encrypt_token(credentials.refresh_token)
        user.google_email = google_email
        user.google_connected_at = datetime.utcnow()
        user.google_token_revoked = False

        await db.commit()

        logger.info(f"Google OAuth connected for user {user.id} ({google_email})")
        return RedirectResponse(f"{frontend_url}/onboarding.html?step=2&google=connected")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save Google credentials: {type(e).__name__}: {e}")
        return RedirectResponse(
            f"{frontend_url}/onboarding.html?google=error&detail=save_failed"
        )


@router.get("/picker-config")
async def get_picker_config(current_user: User = Depends(require_auth)):
    """
    Return config needed for Google Picker JS on the frontend.

    Returns the API key, client ID, and a fresh access token so the
    Picker can show the user's spreadsheets.
    """
    if not current_user.google_refresh_token_encrypted or current_user.google_token_revoked:
        raise HTTPException(status_code=400, detail="Google account not connected")

    if not settings.google_api_key:
        raise HTTPException(status_code=503, detail="Google API key not configured")

    try:
        creds = get_google_credentials(current_user)
        # Force a token refresh to get a valid access token
        from google.auth.transport.requests import Request as GoogleAuthRequest
        creds.refresh(GoogleAuthRequest())

        return {
            "api_key": settings.google_api_key,
            "client_id": settings.google_client_id,
            "access_token": creds.token,
        }
    except Exception as e:
        logger.error(f"Failed to get picker config for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to prepare file picker. Please try again.")


@router.post("/disconnect")
async def disconnect_google(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """
    Disconnect Google account. Revokes token and clears stored credentials.
    """
    # Attempt to revoke the token at Google
    if current_user.google_refresh_token_encrypted:
        try:
            from app.services.google_tokens import decrypt_token
            import httpx

            refresh_token = decrypt_token(current_user.google_refresh_token_encrypted)
            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": refresh_token},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
        except Exception as e:
            logger.warning(f"Failed to revoke Google token for user {current_user.id}: {e}")

    # Clear stored credentials
    current_user.google_refresh_token_encrypted = None
    current_user.google_email = None
    current_user.google_connected_at = None
    current_user.google_token_revoked = True

    await db.commit()

    return {"success": True, "message": "Google account disconnected"}
