# Quick Start Guide

Get the Invoice Collector running in **under 10 minutes**.

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] Gmail account
- [ ] Google Sheets with invoice data

## 5-Minute Setup

### Step 1: Install (1 min)

```bash
# Clone/download the repo, then:
cd Smart-Invoice-Follow-Up-Workflow
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Google Cloud Setup (3 min)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: "invoice-collector"
3. Enable APIs: **Google Sheets API** + **Gmail API**
4. Create OAuth credentials:
   - Type: Desktop app
   - Download as `client_secret.json`
   - Save to project root

### Step 3: Configure (1 min)

```bash
cp .env.example .env
# Edit .env:
# - Add your spreadsheet ID
# - Add your Gmail address
# - Keep DRY_RUN=true for testing
```

### Step 4: Create Google Sheet (2 min)

Headers (row 1):
```
invoice_id | client_name | client_email | amount | currency | due_date | sent_date | status | notes | last_stage_sent | last_sent_at
```

Add test invoice:
```
INV-001 | John Smith | john@example.com | 2500 | USD | [7 days ago] | [14 days ago] | Overdue | Test | |
```

Get spreadsheet ID from URL and add to `.env`

### Step 5: First Run (1 min)

```bash
python main.py --dry-run
```

- Authenticate with Google (browser opens)
- See what drafts would be created
- Verify everything works

### Step 6: Go Live

```bash
# Edit .env: set DRY_RUN=false
python main.py
```

Check Gmail → Drafts, review, and send!

## Daily Usage

```bash
# Run once per day (or set up cron/scheduler)
python main.py

# Review drafts in Gmail
# Click Send on each one (or personalize first)
```

## Common Commands

```bash
# Dry run (preview only)
python main.py --dry-run

# Verbose logging
python main.py --verbose

# Run tests
pytest

# Help
python main.py --help
```

## What Happens Daily

1. System reads Google Sheets for "Overdue" invoices
2. Calculates days overdue for each
3. Determines which reminder stage (7/14/21/28/35/42 days)
4. Creates Gmail drafts with appropriate template
5. Updates tracking in Google Sheets
6. You review and send drafts manually

## Escalation Timeline

| Days Overdue | What Gets Sent |
|--------------|----------------|
| 7 | Friendly check-in |
| 14 | Direct follow-up |
| 21 | Urgent reminder |
| 28 | Firm tone + call suggestion |
| 35 | Final warning |
| 42 | Collections notice |

## Troubleshooting

**"client_secret.json not found"**
→ Download OAuth credentials from Google Cloud Console

**"No invoices found"**
→ Check spreadsheet ID in `.env` and sheet name

**"403 permissions error"**
→ Enable Gmail API and Sheets API in Google Cloud

**Want more details?**
→ See [SETUP.md](SETUP.md) for complete guide

---

**That's it! You're up and running. 🚀**

The system automates 95% of the work - you just review and send.
