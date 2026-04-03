"""
Gmail API wrapper.

Provides functions for creating email drafts using the user's own OAuth credentials.
"""
import base64
import logging
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


def _gmail_service(creds: Credentials):
    """Build Gmail API service."""
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def create_draft(
    creds: Credentials,
    to: str,
    subject: str,
    body_html: str,
) -> dict:
    """
    Create a Gmail draft.

    Args:
        creds: Google OAuth credentials
        to: Recipient email address
        subject: Email subject line
        body_html: HTML email body

    Returns:
        Dict with 'draft_id' and 'message_id'.
    """
    service = _gmail_service(creds)

    message = MIMEText(body_html, "html")
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    draft = (
        service.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": raw}})
        .execute()
    )

    return {
        "draft_id": draft["id"],
        "message_id": draft["message"]["id"],
    }
