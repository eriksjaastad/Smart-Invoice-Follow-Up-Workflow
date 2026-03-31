"""
Google Sheets API wrapper.

Provides functions for listing, validating, creating, reading, and updating
Google Sheets using the user's own OAuth credentials.
"""
import logging
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Template headers for new invoice tracker sheets
TEMPLATE_HEADERS = [
    "Invoice_Number",
    "Client_Name",
    "Client_Email",
    "Amount",
    "Due_Date",
    "Sent_Date",
    "Paid",
    "Last_Stage_Sent",
    "Last_Sent_At",
]


def _sheets_service(creds: Credentials):
    """Build Google Sheets API service."""
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def _drive_service(creds: Credentials):
    """Build Google Drive API service (for listing spreadsheets)."""
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def list_user_sheets(creds: Credentials) -> list[dict[str, str]]:
    """
    List the user's Google Sheets via Drive API.

    Returns:
        List of dicts with 'id' and 'name' keys.
    """
    service = _drive_service(creds)
    results = (
        service.files()
        .list(
            q="mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
            fields="files(id, name)",
            orderBy="modifiedTime desc",
            pageSize=50,
        )
        .execute()
    )
    files = results.get("files", [])
    return [{"id": f["id"], "name": f["name"]} for f in files]


def validate_sheet_columns(creds: Credentials, sheet_id: str) -> list[str]:
    """
    Read the header row (row 1) of a sheet and return column names.

    Args:
        creds: Google OAuth credentials
        sheet_id: Google Sheet ID

    Returns:
        List of column name strings from row 1.
    """
    service = _sheets_service(creds)
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range="A1:Z1")
        .execute()
    )
    values = result.get("values", [])
    if not values:
        return []
    return [str(v).strip() for v in values[0]]


def create_template_sheet(creds: Credentials) -> dict[str, str]:
    """
    Create a new Google Sheet with the Invoice Tracker template headers.

    Returns:
        Dict with 'sheet_id' and 'sheet_url'.
    """
    service = _sheets_service(creds)

    spreadsheet_body = {
        "properties": {"title": "Invoice Tracker"},
        "sheets": [
            {
                "properties": {"title": "Sheet1"},
                "data": [
                    {
                        "startRow": 0,
                        "startColumn": 0,
                        "rowData": [
                            {
                                "values": [
                                    {
                                        "userEnteredValue": {"stringValue": h},
                                        "userEnteredFormat": {"textFormat": {"bold": True}},
                                    }
                                    for h in TEMPLATE_HEADERS
                                ]
                            }
                        ],
                    }
                ],
            }
        ],
    }

    result = service.spreadsheets().create(body=spreadsheet_body).execute()
    sheet_id = result["spreadsheetId"]
    sheet_url = result["spreadsheetUrl"]

    return {"sheet_id": sheet_id, "sheet_url": sheet_url}


def read_invoice_rows(creds: Credentials, sheet_id: str) -> list[dict[str, Any]]:
    """
    Read all rows from the invoice sheet and return as list of dicts.

    Uses row 1 as headers, remaining rows as data.
    Returns list of dicts keyed by header names, with a '_row_number' field
    (1-indexed, where row 1 = headers, row 2 = first data row).
    """
    service = _sheets_service(creds)
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range="A:Z")
        .execute()
    )
    values = result.get("values", [])
    if len(values) < 2:
        return []

    headers = [str(h).strip() for h in values[0]]
    rows = []
    for i, row in enumerate(values[1:], start=2):
        # Pad row to match header length
        padded = row + [""] * (len(headers) - len(row))
        row_dict = {headers[j]: padded[j] for j in range(len(headers))}
        row_dict["_row_number"] = i
        rows.append(row_dict)

    return rows


def update_row_cells(
    creds: Credentials,
    sheet_id: str,
    row_number: int,
    updates: dict[str, str],
    headers: list[str] | None = None,
) -> None:
    """
    Update specific cells in a row by column name.

    Args:
        creds: Google OAuth credentials
        sheet_id: Google Sheet ID
        row_number: 1-indexed row number
        updates: Dict mapping column names to new values
        headers: Optional pre-fetched headers. If None, reads row 1.
    """
    if not headers:
        headers = validate_sheet_columns(creds, sheet_id)

    service = _sheets_service(creds)
    data = []

    for col_name, value in updates.items():
        if col_name not in headers:
            logger.warning(f"Column '{col_name}' not found in sheet headers, skipping")
            continue
        col_index = headers.index(col_name)
        # Convert 0-indexed column to A1 notation (A=0, B=1, etc.)
        col_letter = chr(ord("A") + col_index) if col_index < 26 else "A"
        cell_range = f"{col_letter}{row_number}"
        data.append({"range": cell_range, "values": [[value]]})

    if data:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=sheet_id,
            body={"valueInputOption": "USER_ENTERED", "data": data},
        ).execute()
