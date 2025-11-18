"""
Google Sheets client for reading and writing invoice data
"""
import os
from datetime import datetime
from typing import List, Optional
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import Invoice
from .config import settings

# Scopes for Google Sheets API (read and write)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_sheets_service():
    """
    Get authenticated Google Sheets API service

    Handles OAuth flow and token caching
    """
    creds = None

    # Load existing credentials if available
    if settings.TOKEN_SHEETS_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(settings.TOKEN_SHEETS_FILE), SCOPES)

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
        with open(settings.TOKEN_SHEETS_FILE, "w") as token:
            token.write(creds.to_json())

    return build("sheets", "v4", credentials=creds)


def read_invoices() -> List[Invoice]:
    """
    Read invoices from Google Sheets

    Expected columns:
    - invoice_id
    - client_name
    - client_email
    - amount
    - currency
    - due_date
    - sent_date
    - status
    - notes (optional)
    - last_stage_sent (optional)
    - last_sent_at (optional)

    Returns:
        List of Invoice objects
    """
    try:
        service = _get_sheets_service()
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=settings.SPREADSHEET_ID, range=settings.RANGE)
            .execute()
        )
        values = result.get("values", [])

        if not values:
            return []

        # First row is headers
        headers = [h.strip().lower() for h in values[0]]
        rows = values[1:]

        # Create DataFrame for easier processing
        df = pd.DataFrame(rows, columns=headers)

        # Handle missing columns
        required_cols = [
            "invoice_id",
            "client_name",
            "client_email",
            "amount",
            "currency",
            "due_date",
            "sent_date",
            "status",
        ]
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns in spreadsheet: {missing}")

        # Add optional columns if they don't exist
        for col in ["notes", "last_stage_sent", "last_sent_at"]:
            if col not in df.columns:
                df[col] = None

        # Type conversions
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)

        # Parse dates
        df["due_date"] = pd.to_datetime(df["due_date"], errors="coerce")
        df["sent_date"] = pd.to_datetime(df["sent_date"], errors="coerce")
        df["last_sent_at"] = pd.to_datetime(df["last_sent_at"], errors="coerce")

        # Parse last_stage_sent as integer
        df["last_stage_sent"] = pd.to_numeric(df["last_stage_sent"], errors="coerce")

        # Convert to Invoice objects
        invoices = []
        for idx, row in df.iterrows():
            try:
                invoice = Invoice(
                    invoice_id=str(row.get("invoice_id", "")).strip(),
                    client_name=str(row.get("client_name", "")).strip(),
                    client_email=str(row.get("client_email", "")).strip(),
                    amount=float(row.get("amount", 0.0)),
                    currency=str(row.get("currency", "USD")).strip(),
                    due_date=row["due_date"].date() if pd.notna(row["due_date"]) else None,
                    sent_date=row["sent_date"].date() if pd.notna(row["sent_date"]) else None,
                    status=str(row.get("status", "")).strip(),
                    notes=str(row.get("notes", "")) if pd.notna(row.get("notes")) else "",
                    last_stage_sent=int(row["last_stage_sent"])
                    if pd.notna(row.get("last_stage_sent"))
                    else None,
                    last_sent_at=row["last_sent_at"].date()
                    if pd.notna(row.get("last_sent_at"))
                    else None,
                )
                invoices.append(invoice)
            except (ValueError, TypeError) as e:
                # Skip invalid rows but log the error
                print(f"Warning: Skipping row {idx + 2}: {e}")
                continue

        return invoices

    except HttpError as e:
        raise Exception(f"Error reading from Google Sheets: {e}")


def write_back_invoices(invoice_updates: List[tuple[str, int, str]]) -> int:
    """
    Write back last_stage_sent and last_sent_at to Google Sheets

    Args:
        invoice_updates: List of tuples (invoice_id, stage_sent, sent_date_str)

    Returns:
        Number of rows updated
    """
    if not invoice_updates:
        return 0

    try:
        service = _get_sheets_service()

        # First, read all data to find row numbers for each invoice_id
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=settings.SPREADSHEET_ID, range=settings.RANGE)
            .execute()
        )
        values = result.get("values", [])

        if not values:
            return 0

        headers = [h.strip().lower() for h in values[0]]

        # Find column indices for last_stage_sent and last_sent_at
        try:
            invoice_id_col = headers.index("invoice_id")
            last_stage_col = headers.index("last_stage_sent")
            last_sent_col = headers.index("last_sent_at")
        except ValueError as e:
            raise ValueError(f"Required columns not found in spreadsheet: {e}")

        # Build updates
        updates = []
        for invoice_id, stage, sent_date in invoice_updates:
            # Find the row for this invoice
            for row_idx, row in enumerate(values[1:], start=2):  # Start at row 2 (after header)
                if len(row) > invoice_id_col and row[invoice_id_col] == invoice_id:
                    # Convert column index to letter
                    stage_cell = _column_letter(last_stage_col + 1) + str(row_idx)
                    date_cell = _column_letter(last_sent_col + 1) + str(row_idx)

                    updates.append(
                        {"range": stage_cell, "values": [[stage]]}
                    )
                    updates.append(
                        {"range": date_cell, "values": [[sent_date]]}
                    )
                    break

        if not updates:
            return 0

        # Batch update
        body = {"valueInputOption": "USER_ENTERED", "data": updates}
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=settings.SPREADSHEET_ID, body=body
        ).execute()

        return len(invoice_updates)

    except HttpError as e:
        raise Exception(f"Error writing to Google Sheets: {e}")


def _column_letter(col_num: int) -> str:
    """Convert column number to letter (1=A, 2=B, ..., 27=AA, etc.)"""
    result = ""
    while col_num > 0:
        col_num -= 1
        result = chr(col_num % 26 + ord('A')) + result
        col_num //= 26
    return result
