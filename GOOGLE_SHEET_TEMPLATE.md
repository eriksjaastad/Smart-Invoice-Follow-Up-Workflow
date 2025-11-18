# Google Sheets Template for Invoice Tracking

## Quick Setup

Create a new Google Sheet with these exact column headers in row 1:

```
invoice_id | client_name | client_email | amount | currency | due_date | sent_date | status | notes | last_stage_sent | last_sent_at
```

## Column Details

| Column Name | Type | Required | Description | Example |
|-------------|------|----------|-------------|---------|
| **invoice_id** | Text | ✅ Yes | Unique identifier for the invoice | `INV-001`, `2025-001` |
| **client_name** | Text | ✅ Yes | Full name of the client | `John Smith`, `Acme Corp` |
| **client_email** | Email | ✅ Yes | Email address for reminders | `john@example.com` |
| **amount** | Number | ✅ Yes | Invoice amount (no $ or commas) | `2500`, `10000.50` |
| **currency** | Text | ✅ Yes | Currency code | `USD`, `EUR`, `GBP` |
| **due_date** | Date | ✅ Yes | When payment is/was due | `01/15/2025` |
| **sent_date** | Date | ✅ Yes | When invoice was sent | `01/01/2025` |
| **status** | Text | ✅ Yes | Current status (use "Overdue" for reminders) | `Overdue`, `Paid`, `Open` |
| **notes** | Text | ❌ No | Optional notes | `Project X`, `Net 30` |
| **last_stage_sent** | Number | ❌ No | Last reminder stage (auto-filled) | `7`, `14`, `21` |
| **last_sent_at** | Date | ❌ No | Last reminder date (auto-filled) | `01/22/2025` |

## Sample Data

Here's example data you can copy to test:

| invoice_id | client_name | client_email | amount | currency | due_date | sent_date | status | notes | last_stage_sent | last_sent_at |
|------------|-------------|--------------|--------|----------|----------|-----------|--------|-------|-----------------|--------------|
| INV-001 | John Smith | john@example.com | 2500 | USD | 01/08/2025 | 01/01/2025 | Overdue | Website redesign | | |
| INV-002 | Jane Doe | jane@example.com | 5000 | USD | 01/01/2025 | 12/18/2024 | Overdue | Consulting Q4 | | |
| INV-003 | Acme Corp | billing@acme.com | 10000 | USD | 12/25/2024 | 12/18/2024 | Overdue | Annual retainer | | |
| INV-004 | Bob's Shop | bob@shop.com | 1500 | USD | 02/01/2025 | 01/15/2025 | Open | Logo design | | |
| INV-005 | Tech Startup | accounts@startup.com | 7500 | USD | 01/10/2025 | 01/03/2025 | Paid | MVP development | | |

## Important Notes

### Status Field Rules

The system **only processes invoices** with status = `Overdue`

- ✅ **Overdue** - Will trigger automated reminders
- ❌ **Paid** - System ignores
- ❌ **Open** - System ignores (not overdue yet)
- ❌ **Pending** - System ignores
- ❌ **Cancelled** - System ignores

### Date Format

Use consistent date formatting:
- **Recommended**: `MM/DD/YYYY` (e.g., `01/15/2025`)
- **Also works**: `YYYY-MM-DD` (e.g., `2025-01-15`)

**Important**: Format the date columns as "Date" in Google Sheets, not "Plain Text"

### Auto-Filled Columns

The system automatically fills these columns:

- **last_stage_sent**: Which reminder stage was sent (7, 14, 21, 28, 35, or 42)
- **last_sent_at**: Date the last reminder was sent

**Leave these blank initially** - the system will populate them.

## How the System Works

### Reminder Stages

Based on days overdue, the system sends escalating reminders:

| Days Overdue | Stage | Tone |
|--------------|-------|------|
| 7 days | Stage 1 | Friendly check-in |
| 14 days | Stage 2 | Direct follow-up |
| 21 days | Stage 3 | More urgent |
| 28 days | Stage 4 | Firm reminder |
| 35 days | Stage 5 | Final warning |
| 42 days | Stage 6 | Collections notice |

### Example Timeline

Let's say you sent invoice `INV-001` on January 1st, due January 8th:

- **Jan 8**: Due date passes → Change status to "Overdue"
- **Jan 15** (7 days overdue): System creates Draft #1 (friendly check-in)
- **Jan 22** (14 days overdue): System creates Draft #2 (direct follow-up)
- **Jan 29** (21 days overdue): System creates Draft #3 (urgent)
- **Feb 5** (28 days overdue): System creates Draft #4 (firm)
- **Feb 12** (35 days overdue): System creates Draft #5 (final warning)
- **Feb 19** (42 days overdue): System creates Draft #6 (collections)

Each day, you review drafts in Gmail and click Send (or personalize first).

## Getting Your Spreadsheet ID

1. Open your Google Sheet
2. Look at the URL in your browser:
   ```
   https://docs.google.com/spreadsheets/d/ABC123xyz456_SPREADSHEET_ID_HERE/edit
   ```
3. Copy the part between `/d/` and `/edit` (the spreadsheet ID)
4. Paste it into your `.env` file:
   ```
   GOOGLE_SHEETS_SPREADSHEET_ID=ABC123xyz456_SPREADSHEET_ID_HERE
   ```

## Sheet Naming

By default, the system looks for a sheet named **"Invoices"**.

If your sheet has a different name (like "Invoice Tracker"), update `.env`:

```
GOOGLE_SHEETS_RANGE=Invoice Tracker!A1:Z999
```

## Permissions

Make sure the Google account you authenticate with has **Editor** access to the sheet.

To share:
1. Click "Share" button in Google Sheets
2. Add your Gmail address
3. Set permission to "Editor"

## Tips

### Tracking Paid Invoices

When a client pays:
1. Change status from `Overdue` to `Paid`
2. Add a note: `Paid 01/25/2025 via wire`
3. System will ignore it from now on

### Testing the System

Create a test invoice with:
- `due_date` = 7-14 days ago
- `status` = `Overdue`

Run in dry-run mode to see what draft would be created.

### Bulk Import

If you have existing invoices in QuickBooks, Stripe, or another system:
1. Export to CSV
2. Match columns to this template
3. Import into Google Sheets
4. Ensure dates are formatted correctly
5. Set status to `Overdue` for past-due invoices

---

**Ready to use this template?**

1. Create a new Google Sheet
2. Copy the column headers
3. Add your invoice data
4. Get the spreadsheet ID
5. Configure your `.env` file
6. Run the system!
