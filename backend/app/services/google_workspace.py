"""
Google Workspace delegated Gmail sending.

Uses a service account with domain-wide delegation to send emails via Gmail API.
"""
from __future__ import annotations

import base64
import logging
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

from app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_SCOPES = ("https://www.googleapis.com/auth/gmail.send",)


class GoogleWorkspaceConfigError(RuntimeError):
    """Raised when Google Workspace configuration is missing or invalid."""


def _load_delegated_credentials(
    service_account_file: Path,
    delegated_user: str,
    scopes: Iterable[str] = DEFAULT_SCOPES,
):
    try:
        from google.oauth2 import service_account
    except ImportError as exc:
        raise GoogleWorkspaceConfigError(
            "google-auth is required to use Google Workspace delegated Gmail sending"
        ) from exc

    if not service_account_file.exists():
        raise GoogleWorkspaceConfigError(
            f"Service account file not found: {service_account_file}"
        )

    credentials = service_account.Credentials.from_service_account_file(
        str(service_account_file),
        scopes=list(scopes),
    )
    return credentials.with_subject(delegated_user)


def _get_gmail_service(service_account_file: Path, delegated_user: str):
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise GoogleWorkspaceConfigError(
            "google-api-python-client is required to use Google Workspace delegated Gmail sending"
        ) from exc

    credentials = _load_delegated_credentials(service_account_file, delegated_user)
    return build("gmail", "v1", credentials=credentials)


def send_delegated_email(
    subject: str,
    html_body: str,
    to_emails: str | list[str],
    *,
    sender: str | None = None,
    service_account_file: str | Path | None = None,
    delegated_user: str | None = None,
) -> dict:
    """
    Send an email via Gmail API using a delegated mailbox.

    Args:
        subject: Email subject line
        html_body: HTML body content
        to_emails: Recipient email or list of emails
        sender: Optional From address (defaults to delegated user)
        service_account_file: Path to service account JSON
        delegated_user: Workspace user to impersonate

    Returns:
        Gmail API send response
    """
    if isinstance(to_emails, str):
        recipients = [to_emails]
    else:
        recipients = to_emails

    service_account_path = Path(service_account_file or settings.google_workspace_service_account_file)
    delegated = delegated_user or settings.google_workspace_delegated_user

    if not delegated:
        raise GoogleWorkspaceConfigError("Delegated user is required for Workspace send")

    message = EmailMessage()
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message["From"] = sender or delegated
    message.set_content("This email requires an HTML-capable client.")
    message.add_alternative(html_body, subtype="html")

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    service = _get_gmail_service(service_account_path, delegated)
    result = (
        service.users()
        .messages()
        .send(userId="me", body={"raw": raw_message})
        .execute()
    )

    logger.info("Sent delegated Gmail message to %s (id=%s)", recipients, result.get("id"))
    return result
