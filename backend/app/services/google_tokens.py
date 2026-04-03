"""
Google OAuth token encryption and credential management.

Handles Fernet encryption/decryption of refresh tokens and
building Google API credentials from stored tokens.
"""
import logging

from cryptography.fernet import Fernet, InvalidToken
from google.oauth2.credentials import Credentials

from app.core.config import settings

logger = logging.getLogger(__name__)

# Google OAuth scopes required by the application
# drive.file = only files the user explicitly selects or the app creates (non-sensitive)
# gmail.compose = create drafts (sensitive, but no read access)
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/gmail.compose",
]


def _get_fernet() -> Fernet:
    """Get Fernet instance from configured encryption key."""
    if not settings.google_token_encryption_key:
        raise ValueError("GOOGLE_TOKEN_ENCRYPTION_KEY is not configured")
    return Fernet(settings.google_token_encryption_key.encode())


def encrypt_token(token: str) -> str:
    """Encrypt a refresh token for database storage."""
    f = _get_fernet()
    return f.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a refresh token from database storage."""
    f = _get_fernet()
    try:
        return f.decrypt(encrypted_token.encode()).decode()
    except InvalidToken:
        raise ValueError("Failed to decrypt token — key may have changed")


def get_google_credentials(user) -> Credentials:
    """
    Build Google API credentials from a user's stored refresh token.

    The access token is not stored — it auto-refreshes via the refresh token.

    Args:
        user: User model instance with google_refresh_token_encrypted

    Returns:
        google.oauth2.credentials.Credentials ready for API calls

    Raises:
        ValueError: If user has no stored token or decryption fails
    """
    if not user.google_refresh_token_encrypted:
        raise ValueError(f"User {user.id} has no Google refresh token")

    if user.google_token_revoked:
        raise ValueError(f"User {user.id} Google token has been revoked")

    refresh_token = decrypt_token(user.google_refresh_token_encrypted)

    return Credentials(
        token=None,  # Will be auto-refreshed
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=GOOGLE_SCOPES,
    )
