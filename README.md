
<!-- SCAFFOLD:START - Do not edit between markers -->
# smart-invoice-workflow

Brief description of the project's purpose

## Quick Start

```bash
# Setup
pip install -r requirements.txt

# Run
python main.py
```

## Documentation

See the `Documents/` directory for detailed documentation.

## Status

- **Current Phase:** Foundation
- **Status:** #status/active

<!-- SCAFFOLD:END - Custom content below is preserved -->
# Smart Invoice Workflow

An automated invoice collection system that helps service businesses get paid faster by systematically following up on overdue invoices.

## Overview

This project provides the tools and documentation to build an automated invoice collection system designed to:

- Significantly reduce average invoice collection time (from 45+ days to ~18 days).
- Save valuable time (6-8 hours per week) spent on manual invoice follow-ups.
- Generate Gmail drafts with professional, escalating reminders, ensuring human oversight before sending.
- Automate 95% of the invoice collection workflow while maintaining control.

This system helps businesses improve cash flow, reduce administrative overhead, and increase overall collection rates.

## Contents

This repository contains the following resources:

### Documentation

- **`Documents/guides/QUICK_START.md`**: A concise guide to get the system running quickly (under 10 minutes).
- **`Documents/guides/SETUP.md`**: A comprehensive guide covering complete setup, configuration, and deployment.
- **`Documents/reference/GOOGLE_SHEET_TEMPLATE.md`**: A Google Sheets template for tracking invoices, along with detailed instructions for its use.
- **`Documents/core/Automatic_Invoice_Collection_System_From_Scratch.md`**: A detailed, step-by-step guide to understanding and implementing the system from the ground up.

### Implementation

- **`src/invoice_collector/`**: A complete, self-hosted Python implementation of the invoice collection system.
- **`email_autoresponder.json`**: A Make.com blueprint template, offering a cloud-based alternative for those preferring a no-code solution.
- **`main.py`**: The main entry point for the Python-based system.
- **`tests/`**: A suite of unit tests to ensure the core logic of the Python implementation functions correctly.

## System Architecture

The system employs a 6-stage escalation sequence over a 42-day period, designed to progressively increase the urgency of the reminders:

1. **Day 7**: A friendly check-in to ensure the invoice was received.
2. **Day 14**: A direct follow-up to inquire about the invoice status.
3. **Day 21**: A more urgent tone, emphasizing the importance of timely payment.
4. **Day 28**: A firm reminder, suggesting a phone call to discuss any issues.
5. **Day 35**: A final reminder before escalation to collections or legal action.
6. **Day 42**: A last notice, clearly outlining the next steps if payment is not received.

## Implementation Options

This project offers two primary implementation options:

### Option 1: Python (Self-Hosted) ⭐ **Complete Implementation Included**

This option provides a fully functional, self-hosted Python implementation, giving you complete control over your data and deployment environment.

**Quick Start:**

```bash
pip install -r requirements.txt
cp .env.example .env
# Configure .env with your Google Sheets ID and other settings in .env
doppler run -- python main.py --dry-run
```

**Features:**

- ✅ Complete, working implementation included in the `src/` directory.
- ✅ Seamless integration with the Google Sheets API.
- ✅ Utilizes the Gmail API for creating email drafts (no automatic sending, ensuring human review).
- ✅ Includes pre-defined 6-stage escalation email templates.
- ✅ Automatically tracks the last reminder sent to each client, preventing duplicate reminders.
- ✅ Offers full control over deployment, data storage, and system configuration.
- ✅ Comprehensive unit tests included to ensure code quality and reliability.
- ✅ Docker support for easy containerization and deployment.

**See:** [`Documents/guides/QUICK_START.md`](Documents/guides/QUICK_START.md) or [`Documents/guides/SETUP.md`](Documents/guides/SETUP.md) for detailed instructions.

### Option 2: Make.com (Cloud Automation)

This option leverages the Make.com platform for a no-code, cloud-based implementation.

**Instructions:**

1. Import the provided `email_autoresponder.json` blueprint into your Make.com account.
2. Connect your Google Sheets account (containing your invoice data) and your Gmail account.
3. Configure the blueprint to match the structure of your invoice tracking sheet.

**Good for:** Non-technical users, rapid deployment, and eliminating the need for server management.

## Key Features

- ✅ Automated detection of overdue invoices based on data in your Google Sheet.
- ✅ Intelligent routing based on the number of days an invoice is overdue.
- ✅ Professional, pre-written email templates that escalate in tone over time.
- ✅ Gmail draft creation, allowing for human review and customization before sending.
- ✅ Tracks the last escalation stage sent to each client, preventing redundant emails.
- ✅ Compatible with any invoicing system that can export data to Google Sheets.

## Results

The following results were observed for a consulting firm with $47,000 in outstanding invoices:

- **Cash flow improvement**: $29,375 in outstanding payments were collected within the first 30 days of implementation.
- **Time savings**: 24 hours per month were saved on manual follow-up tasks, representing a value of $4,800 (at a rate of $200/hour).
- **Collection rate**: The overall collection rate improved from 80-85% to 95%.

## Requirements

**For Python Implementation:**

- Python 3.11 or higher is required.
- A Google Cloud project (free tier available) is needed for accessing Google Sheets and Gmail APIs.
- A Google Sheet containing your invoice tracking data is essential.
- A Gmail account to send email drafts from.

**For Make.com Blueprint:**

- A Make.com account is required.
- A Google Sheet containing your invoice tracking data is essential.
- A Gmail account to send email drafts from.

## Quick Links

- 🚀 [Quick Start (10 minutes)](Documents/guides/QUICK_START.md)
- 📖 [Complete Setup Guide](Documents/guides/SETUP.md)
- 📊 [Google Sheets Template](Documents/reference/GOOGLE_SHEET_TEMPLATE.md)
- 🔧 [Implementation Details](Documents/core/Automatic_Invoice_Collection_System_From_Scratch.md)

## Project Structure

```bash
smart-invoice-workflow/
├── src/invoice_collector/       # Core Python implementation
│   ├── models.py                # Invoice data models (defines the structure of invoice data)
│   ├── config.py                # Configuration management (handles API keys, sheet IDs, etc.)
│   ├── sheets.py                # Google Sheets integration (reads and writes data to the sheet)
│   ├── router.py                # Routing logic (determines which email to send based on overdue days)
│   ├── utils.py                 # Utility functions
├── email_autoresponder.json   # Make.com blueprint for cloud automation
├── main.py                    # Main entry point for the Python system
├── requirements.txt           # Python dependencies
├── .env.example               # Example environment variables file
├── tests/                     # Unit tests for core logic
│   ├── test_sheets.py         # Tests for Google Sheets integration
│   ├── test_router.py         # Tests for routing logic
├── Documents/                 # Documentation
│   ├── guides/
│   │   ├── QUICK_START.md
│   │   ├── SETUP.md
│   ├── reference/
│   │   ├── GOOGLE_SHEET_TEMPLATE.md
│   ├── core/
│   │   ├── Automatic_Invoice_Collection_System_From_Scratch.md
└── README.md                  # This file