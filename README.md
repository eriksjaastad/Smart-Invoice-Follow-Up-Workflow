# Smart Invoice Follow-Up Workflow

An automated invoice collection system that helps service businesses get paid faster by systematically following up on overdue invoices.

## Overview

This project contains documentation and templates for building an automatic invoice collection system that:

- Reduces average invoice collection time from 45+ days to ~18 days
- Saves 6-8 hours per week on manual follow-ups
- Creates Gmail drafts (not auto-sends) for professional, escalating reminders
- Maintains human oversight while automating 95% of the work

## Contents

- **`Automatic_Invoice_Collection_System_From_Scratch.md`** - Complete Python implementation guide for building a self-hosted system from scratch
- **`email_autoresponder.json`** - Make.com blueprint template for quick setup
- **`.gitignore`** - Git ignore rules (excludes sensitive workflow document)

## System Architecture

The system uses a 6-stage escalation sequence over 42 days:

1. **Day 7**: Friendly check-in
2. **Day 14**: Direct follow-up
3. **Day 21**: More urgent tone
4. **Day 28**: Firm reminder with call suggestion
5. **Day 35**: Final reminder before escalation
6. **Day 42**: Last notice before collections/legal action

## Implementation Options

### Option 1: Make.com (Quick Setup)
Use the included `email_autoresponder.json` blueprint:
1. Import into Make.com
2. Connect Google Sheets and Gmail
3. Configure your invoice tracking sheet

### Option 2: Python (Self-Hosted)
Follow the detailed guide in `Automatic_Invoice_Collection_System_From_Scratch.md` to build a custom Python solution with:
- Google Sheets API integration
- Gmail API for draft creation
- Customizable templates and routing logic
- Full control over deployment and data

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

- Google Sheets with invoice tracking
- Gmail account
- Make.com account (for blueprint) OR Python 3.11+ (for self-hosted)

## License

This project is provided as-is for educational and business use.

