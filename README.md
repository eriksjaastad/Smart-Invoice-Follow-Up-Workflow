# Smart Invoice Follow-Up Workflow

An automated invoice collection system that helps service businesses get paid faster by systematically following up on overdue invoices.

## Overview

This project contains documentation and templates for building an automatic invoice collection system that:

- Reduces average invoice collection time from 45+ days to ~18 days
- Saves 6-8 hours per week on manual follow-ups
- Creates Gmail drafts (not auto-sends) for professional, escalating reminders
- Maintains human oversight while automating 95% of the work

## Contents

### Documentation
- **`QUICK_START.md`** - Get running in under 10 minutes
- **`SETUP.md`** - Complete setup and deployment guide
- **`GOOGLE_SHEET_TEMPLATE.md`** - Invoice tracking sheet template and instructions
- **`Automatic_Invoice_Collection_System_From_Scratch.md`** - Detailed implementation guide

### Implementation
- **`src/invoice_collector/`** - Complete Python implementation (self-hosted)
- **`email_autoresponder.json`** - Make.com blueprint template (cloud alternative)
- **`main.py`** - Main entry point for the Python system
- **`tests/`** - Unit tests for core logic

## System Architecture

The system uses a 6-stage escalation sequence over 42 days:

1. **Day 7**: Friendly check-in
2. **Day 14**: Direct follow-up
3. **Day 21**: More urgent tone
4. **Day 28**: Firm reminder with call suggestion
5. **Day 35**: Final reminder before escalation
6. **Day 42**: Last notice before collections/legal action

## Implementation Options

### Option 1: Python (Self-Hosted) ⭐ **Complete Implementation Included**

**Quick Start:**
```bash
pip install -r requirements.txt
cp .env.example .env
# Configure .env with your Google Sheets ID
python main.py --dry-run
```

**Features:**
- ✅ Complete working implementation included in `src/`
- ✅ Google Sheets API integration
- ✅ Gmail API for draft creation (no auto-send)
- ✅ 6-stage escalation templates
- ✅ Automatic tracking of last reminder sent
- ✅ Full control over deployment and data
- ✅ Unit tests included
- ✅ Docker support

**See:** [`QUICK_START.md`](QUICK_START.md) or [`SETUP.md`](SETUP.md)

### Option 2: Make.com (Cloud Automation)

Use the included `email_autoresponder.json` blueprint:
1. Import into Make.com
2. Connect Google Sheets and Gmail
3. Configure your invoice tracking sheet

**Good for:** Non-technical users, quick setup, no server management

## Key Features

- ✅ Automated overdue invoice detection
- ✅ Smart routing based on days overdue
- ✅ Professional, escalating email templates
- ✅ Gmail draft creation (human review before sending)
- ✅ Tracks last stage sent to prevent duplicates
- ✅ Works with any invoicing system using Google Sheets

## Results

For a consulting firm with $47,000 in outstanding invoices:
- **Cash flow improvement**: $29,375 freed up in first 30 days
- **Time savings**: 24 hours/month ($4,800 value at $200/hour)
- **Collection rate**: Improved from 80-85% to 95%

## Requirements

**For Python Implementation:**
- Python 3.11 or higher
- Google Cloud project (free)
- Google Sheets with invoice tracking
- Gmail account

**For Make.com Blueprint:**
- Make.com account
- Google Sheets with invoice tracking
- Gmail account

## Quick Links

- 🚀 [Quick Start (10 minutes)](QUICK_START.md)
- 📖 [Complete Setup Guide](SETUP.md)
- 📊 [Google Sheets Template](GOOGLE_SHEET_TEMPLATE.md)
- 🔧 [Implementation Details](Automatic_Invoice_Collection_System_From_Scratch.md)

## Project Structure

```
Smart-Invoice-Follow-Up-Workflow/
├── src/invoice_collector/       # Core Python implementation
│   ├── models.py                # Invoice data models
│   ├── config.py                # Configuration management
│   ├── sheets.py                # Google Sheets integration
│   ├── router.py                # Routing logic (days → stage)
│   ├── emailer.py               # Gmail draft creation
│   ├── scheduler.py             # Main orchestrator
│   └── templates/               # 6 escalation email templates
├── tests/                       # Unit tests
├── main.py                      # Entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Configuration template
├── Dockerfile                   # Docker deployment
├── QUICK_START.md              # 10-minute setup guide
├── SETUP.md                    # Detailed setup guide
└── GOOGLE_SHEET_TEMPLATE.md    # Spreadsheet template
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src/invoice_collector

# Run specific tests
pytest tests/test_router.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/
```

## License

This project is provided as-is for educational and business use.

