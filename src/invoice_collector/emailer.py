"""
Gmail client for creating email drafts (NOT auto-sending)
Handles template rendering and draft creation via Gmail API
"""
import base64
import re
import time
import logging
from email.mime.text import MIMEText
from pathlib import Path
from string import Template
from typing import Tuple

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import settings

logger = logging.getLogger(__name__)

# Scopes for Gmail API (compose/drafts only, not send)
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


def _get_gmail_service():
    """
    Get authenticated Gmail API service

    Handles OAuth flow and token caching
    """
    creds = None

    # Load existing credentials if available
    if settings.TOKEN_GMAIL_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(settings.TOKEN_GMAIL_FILE), SCOPES)

    # If credentials are invalid or don't exist, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(settings.CLIENT_SECRET_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials for future runs
        with open(settings.TOKEN_GMAIL_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def render_template(template_path: Path, context: dict) -> Tuple[str, str]:
    """
    Render an email template with the given context

    Template format:
    - First line: Subject: {{subject_template}}
    - Blank line
    - Rest: Email body with {{placeholders}}

    Args:
        template_path: Path to the template file
        context: Dictionary of values to substitute

    Returns:
        Tuple of (subject, body)
    """
    with open(template_path, "r", encoding="utf-8") as f:
        raw_content = f.read()

    # Extract Subject line (first line) and body (rest after blank line)
    match = re.match(r"Subject:\s*(.*?)\n\n(.*)", raw_content, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Template {template_path} must start with 'Subject:' line followed by blank line")

    subject_template = match.group(1)
    body_template = match.group(2)

    # Render using simple {{variable}} substitution (compatible with template files)
    def substitute_variables(text: str, context: dict) -> str:
        """Simple template substitution for {{variable}} syntax"""
        result = text
        for key, value in context.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result

    subject = substitute_variables(subject_template, context)
    body = substitute_variables(body_template, context)

    return subject, body


def template_path_for(stage: int) -> Path:
    """
    Get the template file path for a given stage

    Args:
        stage: Stage number (7, 14, 21, 28, 35, or 42)

    Returns:
        Path to the template file
    """
    return settings.TEMPLATES_DIR / f"stage_{stage:02d}.txt"


def create_draft(to_email: str, subject: str, body: str, max_retries: int = None) -> dict:
    """
    Create a Gmail draft (does NOT send the email)
    Includes exponential backoff for rate limiting (429 errors)

    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: Email body text
        max_retries: Maximum number of retry attempts (defaults to settings.MAX_RETRIES)

    Returns:
        Draft creation response from Gmail API
    """
    if max_retries is None:
        max_retries = settings.MAX_RETRIES

    service = _get_gmail_service()

    # Create the email message
    message = MIMEText(body, "plain", "utf-8")
    message["To"] = to_email
    message["From"] = settings.GMAIL_SENDER
    message["Subject"] = subject

    # Encode the message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    draft_body = {"message": {"raw": raw_message}}

    # Retry with exponential backoff for rate limiting
    for attempt in range(max_retries + 1):
        try:
            draft = service.users().drafts().create(userId="me", body=draft_body).execute()
            return draft

        except HttpError as e:
            # Check if it's a rate limit error (429)
            if e.resp.status == 429 and attempt < max_retries:
                wait_time = settings.RETRY_INITIAL_WAIT * (2 ** attempt)  # Exponential backoff
                logger.warning(f"⚠️  Rate limit hit on Gmail API, waiting {wait_time}s before retry (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                # Non-rate-limit error or max retries exceeded
                raise Exception(f"Error creating Gmail draft: {e}")


def create_draft_from_template(
    to_email: str,
    to_name: str,
    stage: int,
    invoice_id: str,
    amount: float,
    currency: str,
    due_date: str
) -> dict:
    """
    Create a Gmail draft from a template with invoice data

    Args:
        to_email: Recipient email address
        to_name: Recipient name
        stage: Reminder stage (7, 14, 21, 28, 35, or 42)
        invoice_id: Invoice identifier
        amount: Invoice amount
        currency: Currency code
        due_date: Due date formatted as string

    Returns:
        Draft creation response from Gmail API
    """
    # Build context for template
    context = {
        "name": to_name,
        "invoice_id": invoice_id,
        "amount": f"{amount:,.2f}",
        "currency": currency,
        "due_date": due_date,
    }

    # Render template
    template_file = template_path_for(stage)
    subject, body = render_template(template_file, context)

    # Create draft
    return create_draft(to_email, subject, body)
