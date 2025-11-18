# Setup Guide - Invoice Collector

Complete setup instructions for the Smart Invoice Follow-Up Workflow Python implementation.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Google Cloud Setup](#google-cloud-setup)
4. [Google Sheets Setup](#google-sheets-setup)
5. [Configuration](#configuration)
6. [First Run](#first-run)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- **Python 3.11 or higher**
- **Google Account** with access to Gmail and Google Sheets
- **Google Cloud Project** (we'll create this)
- **pip** or **uv** for package management

---

## Installation

### Option 1: Using pip (Standard)

```bash
# Clone or download this repository
cd Smart-Invoice-Follow-Up-Workflow

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Option 2: Using uv (Faster)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

---

## Google Cloud Setup

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Create Project"**
3. Name it something like `invoice-collector`
4. Click **"Create"**

### 2. Enable Required APIs

1. In your project, go to **"APIs & Services"** → **"Library"**
2. Search for and enable:
   - **Google Sheets API**
   - **Gmail API**

### 3. Create OAuth Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"OAuth client ID"**
3. If prompted, configure the OAuth consent screen:
   - User Type: **External** (unless you have a workspace)
   - App name: `Invoice Collector`
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: Add `../auth/gmail.compose` and `../auth/spreadsheets`
   - Test users: Add your Gmail address
4. Create credentials:
   - Application type: **Desktop app**
   - Name: `Invoice Collector Desktop`
5. Click **"Create"**
6. Click **"Download JSON"**
7. **Rename the downloaded file to `client_secret.json`**
8. **Move it to the project root directory** (same folder as `main.py`)

⚠️ **IMPORTANT**: Never commit `client_secret.json` to git. It's already in `.gitignore`.

---

## Google Sheets Setup

### 1. Create Your Invoice Tracking Sheet

Create a new Google Sheet with these **exact column headers** in row 1:

| invoice_id | client_name | client_email | amount | currency | due_date | sent_date | status | notes | last_stage_sent | last_sent_at |
|------------|-------------|--------------|--------|----------|----------|-----------|--------|-------|-----------------|--------------|

### 2. Column Descriptions

- **invoice_id**: Unique identifier (e.g., `INV-001`, `2025-001`)
- **client_name**: Client's full name
- **client_email**: Where to send reminders
- **amount**: Invoice amount (numbers only, no $ or commas)
- **currency**: Currency code (`USD`, `EUR`, `GBP`, etc.)
- **due_date**: Due date in format `MM/DD/YYYY` or `YYYY-MM-DD`
- **sent_date**: Date invoice was sent
- **status**: Current status - use `Overdue` to trigger reminders
- **notes**: Optional notes about the invoice
- **last_stage_sent**: Leave blank (system fills this in)
- **last_sent_at**: Leave blank (system fills this in)

### 3. Example Data

Here's a sample row to test with:

| invoice_id | client_name | client_email | amount | currency | due_date | sent_date | status | notes | last_stage_sent | last_sent_at |
|------------|-------------|--------------|--------|----------|----------|-----------|--------|-------|-----------------|--------------|
| INV-001 | John Smith | john@example.com | 2500 | USD | 01/15/2025 | 01/01/2025 | Overdue | Project X | | |

### 4. Get Your Spreadsheet ID

1. Open your Google Sheet
2. Look at the URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit`
3. Copy the `SPREADSHEET_ID_HERE` part
4. Save it - you'll need it for configuration

### 5. Share Sheet (if needed)

Make sure the Google account you'll authenticate with has **Editor** access to this sheet.

---

## Configuration

### 1. Create `.env` File

Copy the example environment file:

```bash
cp .env.example .env
```

### 2. Edit `.env` with Your Settings

```bash
# Replace with your spreadsheet ID from the previous step
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here

# Adjust the range if your sheet is named differently (default: "Invoices")
GOOGLE_SHEETS_RANGE=Invoices!A1:Z999

# Your Gmail address (where drafts will be created FROM)
GMAIL_SENDER=you@yourdomain.com

# Start in dry-run mode to test safely
DRY_RUN=true

# Optional: Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Optional: Business hours (24-hour format)
WINDOW_START=8
WINDOW_END=18
```

---

## First Run

### 1. Test Installation

```bash
# Verify Python packages
python -c "import pandas, googleapiclient; print('✅ Packages installed correctly')"
```

### 2. Run in Dry-Run Mode

```bash
python main.py --dry-run --verbose
```

**What will happen:**
1. Browser will open for Google OAuth consent (do this twice - once for Sheets, once for Gmail)
2. Grant permissions to:
   - Read/write your Google Sheets
   - Create Gmail drafts (NOT send emails)
3. System will analyze your invoices
4. You'll see what drafts **would** be created (but nothing actually created yet)

### 3. Review Output

You should see output like:

```
================================================================================
📧 Created 3 Gmail Draft(s)
================================================================================
Invoice ID    Stage    Client        Email                  Amount         Days Overdue
------------  -------  ------------  -------------------  -------------  --------------
INV-001       Day 7    John Smith    john@example.com      $2,500.00 USD  7d overdue
INV-002       Day 14   Jane Doe      jane@example.com      $5,000.00 USD  14d overdue
INV-003       Day 21   Acme Corp     billing@acme.com     $10,000.00 USD  21d overdue
================================================================================

⚠️  DRY RUN MODE - No actual drafts were created
   Set DRY_RUN=false in .env to create real drafts
```

### 4. Run for Real

When you're ready to create actual drafts:

1. Edit `.env` and set `DRY_RUN=false`
2. Run: `python main.py`
3. Open Gmail → Drafts
4. Review and send the drafts manually

---

## Deployment

### Option 1: Daily Cron Job (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 9:00 AM
0 9 * * * cd /path/to/Smart-Invoice-Follow-Up-Workflow && /path/to/.venv/bin/python main.py >> logs/cron.log 2>&1
```

### Option 2: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 9:00 AM
4. Action: Start a program
   - Program: `C:\path\to\.venv\Scripts\python.exe`
   - Arguments: `main.py`
   - Start in: `C:\path\to\Smart-Invoice-Follow-Up-Workflow`

### Option 3: Docker

```bash
# Build image
docker build -t invoice-collector .

# Run with environment variables
docker run -v $(pwd)/.env:/app/.env \
           -v $(pwd)/client_secret.json:/app/client_secret.json \
           -v $(pwd)/token_sheets.json:/app/token_sheets.json \
           -v $(pwd)/token_gmail.json:/app/token_gmail.json \
           invoice-collector
```

---

## Troubleshooting

### "Configuration errors: GOOGLE_SHEETS_SPREADSHEET_ID is required"

**Fix**: Edit `.env` and add your spreadsheet ID

### "client_secret.json not found"

**Fix**: Download OAuth credentials from Google Cloud Console and save as `client_secret.json` in project root

### "invalid_grant" error

**Fix**: Delete `token_sheets.json` and `token_gmail.json`, then run again to re-authenticate

### "403 insufficientPermissions"

**Fix**: Make sure you enabled both Gmail API and Google Sheets API in Google Cloud Console

### Empty reads / No invoices found

**Fix**:
- Verify `GOOGLE_SHEETS_SPREADSHEET_ID` is correct
- Check `GOOGLE_SHEETS_RANGE` matches your sheet name (default: "Invoices")
- Ensure your Google account has Editor access to the sheet

### Dates not parsing correctly

**Fix**:
- Use consistent date format in Google Sheets: `MM/DD/YYYY` or `YYYY-MM-DD`
- Format the column as "Date" in Google Sheets (not "Plain Text")

### Gmail quota errors (429)

**Fix**:
- Reduce frequency of runs
- Only run during business hours
- Batch process in smaller groups

---

## Daily Operating Procedure

Once set up, here's your daily 5-minute routine:

1. **Open Gmail → Drafts**
2. **Scan subject lines** - identify high-value invoices
3. **Open each draft** and personalize first line if needed
4. **Click Send** (or delete if invoice was already paid)
5. **Done!** The system handles tracking automatically

---

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/invoice_collector

# Run specific test file
pytest tests/test_router.py -v
```

---

## Next Steps

- Customize email templates in `src/invoice_collector/templates/`
- Adjust escalation timing by modifying `STAGES` in `config.py`
- Add Stripe payment links to templates
- Set up Slack notifications for high-value invoices
- Integrate with QuickBooks or other accounting systems

---

## Support

- Check the main [README.md](README.md) for project overview
- See implementation guide: [Automatic_Invoice_Collection_System_From_Scratch.md](Automatic_Invoice_Collection_System_From_Scratch.md)
- For issues, check the troubleshooting section above

---

**You're all set! 🚀**

Start with dry-run mode, verify everything works, then switch to production and let the system handle your invoice follow-ups.
