# Design Document: Smart Invoice SaaS MVP

## Overview

Smart Invoice is a hosted SaaS application that transforms an existing Python CLI tool into a web service for automated invoice follow-up. The system uses Make.com as the automation layer to handle Google OAuth, Sheets API, Gmail API, and daily scheduling, while a FastAPI backend manages user accounts, billing, and weekly digest emails.

The architecture follows a clear separation of concerns:
- **Make.com**: Handles all Google API interactions, OAuth token management, and daily job scheduling. Scenarios are stateless, storing only user_id as a build variable.
- **FastAPI Backend**: Single source of truth for all user config and plan data. Provides config API for scenarios and receives webhook results.
- **PostgreSQL**: Stores user data, Make.com scenario IDs, and job execution logs
- **Vercel**: Hosts the serverless backend (no background job support needed)
- **Static HTML + Alpine.js/htmx**: Minimal frontend for landing page and 4-step onboarding flow

This design reuses the proven escalation logic from the existing CLI (7 source files, 41 tests) while adding web-based user management and billing capabilities.

**Architecture Decision (2026-02-14)**: Stateless scenarios with backend as brain. Each scenario stores only user_id and fetches all config via GET /api/users/{user_id}/config at runtime. Results posted back via POST /api/webhooks/make-results.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     User's Browser                           │
│  ┌────────────┐         ┌──────────────┐                    │
│  │  Landing   │────────▶│   Signup     │                    │
│  │   Page     │         │   Flow       │                    │
│  └────────────┘         └──────┬───────┘                    │
└────────────────────────────────┼──────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Vercel)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐       │
│  │    Auth      │  │   Billing    │  │   Digest    │       │
│  │   Routes     │  │   (Stripe)   │  │   Service   │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘       │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            ▼                                 │
│                   ┌─────────────────┐                        │
│                   │   PostgreSQL    │                        │
│                   │   (Users, Jobs) │                        │
│                   └─────────────────┘                        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ Create/Configure Scenario
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Make.com Platform                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         User's Make.com Scenario (Daily)             │   │
│  │                                                       │   │
│  │  1. Read Google Sheet ────────────────────┐          │   │
│  │  2. Calculate days overdue                │          │   │
│  │  3. Determine escalation stage            │          │   │
│  │  4. Create Gmail drafts                   │          │   │
│  │  5. Update sheet tracking                 │          │   │
│  │  6. Log results to our API                │          │   │
│  │                                            │          │   │
│  └────────────────────────────────────────────┼──────────┘   │
│                                               │              │
│         ┌─────────────────────────────────────┘              │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │   Google     │         │    Gmail     │                  │
│  │   Sheets     │         │     API      │                  │
│  │     API      │         │              │                  │
│  └──────────────┘         └──────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Onboarding Flow**:
   - User signs up on landing page → FastAPI creates user account
   - User redirects to Make.com OAuth → Make.com handles Google authorization
   - Make.com callback → FastAPI receives scenario ID and stores it
   - User selects sheet → FastAPI validates columns via Make.com API
   - User provides name/business → FastAPI stores Sender_Info

2. **Daily Processing Flow**:
   - Make.com scheduler triggers user's scenario (once per day)
   - Scenario calls GET /api/users/{user_id}/config to fetch sheet_id, sender info, plan, and invoice_limit
   - Scenario reads Invoice_Sheet via Google Sheets API (limited by invoice_limit)
   - Scenario calculates days_overdue and determines Escalation_Stage
   - Scenario creates Gmail_Drafts via Gmail API
   - Scenario updates Invoice_Sheet tracking columns
   - Scenario uses Numeric Aggregator to sum amounts and count drafts
   - Scenario POSTs results to /api/webhooks/make-results with user_id, drafts_created, total_outstanding_amount
   - FastAPI stores job history in PostgreSQL

3. **Weekly Digest Flow**:
   - Cron job (external service like cron-job.org or Vercel Cron) hits FastAPI endpoint every Monday
   - FastAPI queries job history for past 7 days per user
   - FastAPI aggregates drafts_created and total_outstanding_amount from webhook data
   - FastAPI sends digest email via SendGrid/Mailgun
   - Digest includes drafts created, outstanding amount, critical invoices

4. **Billing Flow**:
   - User clicks upgrade → FastAPI creates Stripe Checkout session
   - User completes payment → Stripe webhook notifies FastAPI
   - FastAPI updates user plan to Paid_Tier
   - Next Make.com scenario run fetches updated config via GET /api/users/{user_id}/config
   - Scenario receives invoice_limit=100 and processes all invoices

## Components and Interfaces

### 1. FastAPI Backend

**Responsibilities**:
- User authentication (email/password or magic link)
- User account CRUD operations
- Make.com scenario creation/configuration via Make.com API
- Stripe Checkout session creation
- Stripe webhook handling
- Weekly digest email generation
- Job history storage and retrieval
- Error notification emails

**API Routes**:

```python
# Authentication (Auth0 - managed auth, non-negotiable)
GET    /api/auth/callback          # Handle Auth0 callback
GET    /api/auth/logout            # Logout user
GET    /api/auth/me                # Get current user profile

# Onboarding
POST   /api/onboarding/connect-google    # Initiate Make.com OAuth
GET    /api/onboarding/callback          # Handle Make.com callback
GET    /api/onboarding/sheets            # List user's Google Sheets
POST   /api/onboarding/select-sheet      # Validate and store sheet_id
POST   /api/onboarding/sender-info       # Store name and business_name

# User Config API (called by Make.com scenarios)
GET    /api/users/{user_id}/config       # Return sheet_id, sender_name, business_name, plan, invoice_limit

# Billing
POST   /api/billing/create-checkout      # Create Stripe Checkout session
POST   /api/billing/webhook              # Handle Stripe webhooks
GET    /api/billing/status               # Get user's billing status

# Webhooks (from Make.com)
POST   /api/webhooks/make-results        # Receive job results: user_id, drafts_created, total_outstanding_amount

# Weekly Digest (triggered by external cron)
POST   /api/digest/send                  # Send weekly digests to all users

# Health
GET    /api/health                       # Health check endpoint
```

**Environment Variables**:
```
DATABASE_URL=postgresql://...
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=...
AUTH0_CLIENT_SECRET=...
AUTH0_AUDIENCE=https://api.smartinvoice.com
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
MAKE_API_KEY=...
MAKE_SCENARIO_TEMPLATE_ID=...
MAKE_WEBHOOK_API_KEY=...
SENDGRID_API_KEY=...
FRONTEND_URL=https://...
```

**Note on Auth0**: Auth0 is a deliberate, non-negotiable decision for managed authentication. Do NOT replace with custom JWT or homebrew auth solutions. Security is paramount.

**Note on Make.com Architecture**: Scenarios are stateless. They store only user_id as a build variable and fetch all config via GET /api/users/{user_id}/config at runtime.

### 2. Make.com Scenario

**Responsibilities**:
- Execute daily for each user (scheduled trigger)
- Read Invoice_Sheet via Google Sheets API
- Calculate days_overdue for each invoice
- Determine Escalation_Stage based on days_overdue
- Filter invoices based on Free_Tier/Paid_Tier limits
- Create Gmail_Drafts with personalized content
- Update Invoice_Sheet tracking columns
- POST job results to FastAPI webhook

**Scenario Structure**:

```
1. Trigger: Schedule (daily at 9 AM user's timezone)
2. Module: HTTP GET - Fetch User Config
   - URL: {{api_url}}/api/users/{{user_id}}/config
   - Headers: Authorization: Bearer {{api_key}}
   - Output: sheet_id, sender_name, business_name, plan, invoice_limit
3. Module: Google Sheets - Search Rows
   - Spreadsheet ID: {{config.sheet_id}}
   - Limit: {{config.invoice_limit}} (3 for free, 100 for paid)
   - Filter: status = "Overdue" OR status = "Open"
4. Module: Iterator (loop through rows)
5. Module: Custom Function - Calculate Days Overdue
   - Input: due_date, current_date
   - Output: days_overdue
6. Module: Custom Function - Determine Stage
   - Input: days_overdue
   - Output: stage (7, 14, 21, 28, 35, 42, or null)
7. Module: Router - Check if Draft Needed
   - Route 1: stage > last_stage_sent AND last_sent_at != today
   - Route 2: Skip (no draft needed)
8. Module: Gmail - Create Draft
   - To: {{client_email}}
   - Subject: "Re: Invoice {{invoice_id}}"
   - Body: {{template[stage]}} with {{config.sender_name}} and {{config.business_name}}
9. Module: Google Sheets - Update Row
   - Set last_stage_sent = {{stage}}
   - Set last_sent_at = {{current_date}}
10. Module: Numeric Aggregator - Sum Amounts and Count Drafts
    - Sum: {{amount}} field
    - Count: number of processed invoices
11. Module: HTTP POST - Send Results to Backend
    - URL: {{api_url}}/api/webhooks/make-results
    - Headers: Authorization: Bearer {{api_key}}
    - Body: {user_id, drafts_created, total_outstanding_amount}
```

**Configuration Variables** (per user):
- `user_id`: UUID from our database (only thing stored in scenario as build variable)
- `api_url`: Our FastAPI backend URL
- `api_key`: Authentication token for API calls

**Stateless Design**: The scenario fetches all user config (sheet_id, sender info, plan, limits) from our backend at runtime via GET /api/users/{user_id}/config. This ensures the backend is the single source of truth.

### 3. PostgreSQL Database

**Schema**:

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth0_user_id TEXT UNIQUE NOT NULL,  -- Auth0 user identifier (e.g., "auth0|123456")
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    business_name TEXT NOT NULL,
    sheet_id TEXT,
    make_scenario_id TEXT,
    active BOOLEAN DEFAULT true,
    plan TEXT DEFAULT 'free' CHECK (plan IN ('free', 'paid')),
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    last_run_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Job history table
CREATE TABLE job_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    run_at TIMESTAMP DEFAULT NOW(),
    invoices_checked INTEGER NOT NULL,
    drafts_created INTEGER NOT NULL,
    errors JSONB,  -- Array of error objects
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_auth0 ON users(auth0_user_id);
CREATE INDEX idx_users_make_scenario ON users(make_scenario_id);
CREATE INDEX idx_job_history_user ON job_history(user_id);
CREATE INDEX idx_job_history_run_at ON job_history(run_at);
```

### 4. Email Templates

**Gmail Draft Templates** (6 stages):

Each template includes these variables:
- `{{client_name}}`: Client's name from sheet
- `{{invoice_id}}`: Invoice identifier
- `{{amount}}`: Invoice amount with currency
- `{{days_overdue}}`: Number of days overdue
- `{{sender_name}}`: User's name
- `{{sender_business}}`: User's business name

Templates are stored in Make.com scenario as text constants (reuse existing CLI templates from `src/invoice_collector/templates/`).

**Weekly Digest Template**:

```
Subject: Your Smart Invoice Weekly Summary

Hi {{user_name}},

Here's what happened with your invoices this week:

📧 Drafts Created: {{drafts_count}}
💰 Total Outstanding: {{total_amount}}
⚠️  Critical Invoices (35+ days): {{critical_count}}

{{#if free_tier_limit_reached}}
🔓 You've reached your free tier limit (3 invoices). 
   Upgrade to process all your overdue invoices: {{upgrade_url}}
{{/if}}

Next Steps:
1. Review your Gmail drafts
2. Send or edit as needed
3. We'll continue monitoring your invoices

Questions? Reply to this email.

Best,
The Smart Invoice Team
```

**Error Notification Template**:

```
Subject: Action Required: Smart Invoice Connection Issue

Hi {{user_name}},

We encountered an issue with your Smart Invoice automation:

Error: {{error_type}}
Details: {{error_message}}

What to do:
{{resolution_steps}}

Need help? Reply to this email.

Best,
The Smart Invoice Team
```

## Data Models

### User Model

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from uuid import UUID

class User(BaseModel):
    id: UUID
    auth0_user_id: str  # Auth0 user identifier
    email: EmailStr
    name: str
    business_name: str
    sheet_id: Optional[str] = None
    make_scenario_id: Optional[str] = None
    active: bool = True
    plan: str = "free"  # "free" or "paid"
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    created_at: datetime
    last_run_at: Optional[datetime] = None
    updated_at: datetime

class UserCreate(BaseModel):
    auth0_user_id: str
    email: EmailStr
    name: str
    business_name: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    business_name: Optional[str] = None
    sheet_id: Optional[str] = None
    make_scenario_id: Optional[str] = None
    active: Optional[bool] = None
    plan: Optional[str] = None
```

### Job History Model

```python
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel
from uuid import UUID

class JobError(BaseModel):
    invoice_id: str
    error_type: str
    error_message: str

class JobHistory(BaseModel):
    id: UUID
    user_id: UUID
    run_at: datetime
    invoices_checked: int
    drafts_created: int
    errors: Optional[List[JobError]] = []
    duration_ms: Optional[int] = None
    created_at: datetime

class JobLogRequest(BaseModel):
    user_id: UUID
    invoices_checked: int
    drafts_created: int
    errors: Optional[List[JobError]] = []
    duration_ms: Optional[int] = None
```

### Invoice Model (for Make.com processing)

```python
from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr

class Invoice(BaseModel):
    """
    Represents an invoice row from Google Sheet
    (processed in Make.com, not stored in our database)
    """
    invoice_id: str
    client_name: str
    client_email: EmailStr
    amount: float
    currency: str
    due_date: date
    sent_date: date
    status: str
    notes: Optional[str] = ""
    last_stage_sent: Optional[int] = None
    last_sent_at: Optional[date] = None

    def days_overdue(self, today: date = None) -> int:
        """Calculate days overdue"""
        if today is None:
            today = date.today()
        return max(0, (today - self.due_date).days)
```

### Escalation Logic (ported from CLI)

```python
from typing import Optional

# Stage thresholds (days overdue)
STAGES = [7, 14, 21, 28, 35, 42]

def stage_for(days: int) -> Optional[int]:
    """
    Determine which reminder stage based on days overdue
    
    Returns:
        Stage number (7, 14, 21, 28, 35, 42) or None if < 7 days
    """
    eligible_stages = [s for s in STAGES if days >= s]
    return max(eligible_stages) if eligible_stages else None

def should_send_draft(
    stage: Optional[int],
    last_stage_sent: Optional[int],
    last_sent_at: Optional[date],
    today: date = None
) -> bool:
    """
    Determine if a draft should be created
    
    Rules:
    1. No stage determined (< 7 days overdue) → False
    2. Already sent today → False
    3. Never sent before → True
    4. Current stage > last stage sent → True
    5. Otherwise → False
    """
    if today is None:
        today = date.today()
    
    if stage is None:
        return False
    
    if last_sent_at == today:
        return False
    
    if last_stage_sent is None:
        return True
    
    return stage > last_stage_sent
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, I've identified several areas where properties can be consolidated:

**Escalation Stage Assignment (6.1-6.7)**: These seven criteria all test the same `stage_for()` function with different input ranges. They can be combined into a single comprehensive property that tests the stage assignment logic across all possible days_overdue values.

**Draft Creation Logic (7.1-7.5)**: These five criteria all test the `should_send_draft()` function. They can be combined into a single property that tests all the decision rules together.

**User Account Creation (1.1, 1.4, 1.5)**: These test account creation, data persistence, and default plan. They can be combined into one property that verifies complete account creation behavior.

**Sheet Validation (3.2, 3.3, 3.4)**: These all test the sheet validation logic. They can be combined into a property that tests validation across various column configurations.

**Job History Logging (17.1, 17.2, 17.3)**: These test job history record creation and completeness. They can be combined into one property.

**Weekly Digest Content (13.2, 13.3, 13.4, 13.5, 13.6)**: These all test digest email content generation. They can be combined into a property that verifies all required content is present.

**Make.com Scenario Management (19.1, 19.2, 19.3)**: These test scenario creation and configuration. They can be combined into one property.

**Data Privacy (20.1, 20.3, 20.4)**: These test what data is and isn't stored. They can be combined into one property about database schema constraints.

### Correctness Properties

Property 1: Days Overdue Calculation
*For any* invoice with a due_date and a reference date (today), calculating days_overdue should return max(0, today - due_date) in days
**Validates: Requirements 5.3**

Property 2: Escalation Stage Assignment
*For any* number of days_overdue, the assigned escalation stage should be: None if < 7 days, 7 if 7-13 days, 14 if 14-20 days, 21 if 21-27 days, 28 if 28-34 days, 35 if 35-41 days, or 42 if >= 42 days
**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7**

Property 3: Draft Creation Decision Logic
*For any* invoice with a current stage, last_stage_sent, and last_sent_at, a draft should be created if and only if: (1) current stage is not None, AND (2) last_sent_at is not today, AND (3) either last_stage_sent is None OR current stage > last_stage_sent
**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**

Property 4: Free Tier Invoice Limit
*For any* set of overdue invoices where the user has plan="free", processing should handle at most 3 invoices, selecting those with the highest days_overdue values
**Validates: Requirements 10.1, 10.2, 10.3**

Property 5: Paid Tier Unlimited Processing
*For any* set of overdue invoices where the user has plan="paid", all invoices should be processed without limit
**Validates: Requirements 11.1**

Property 6: Account Creation with Defaults
*For any* valid Auth0 user profile (auth0_user_id, email, name) and business_name, creating a user account should result in a stored record with all provided fields plus plan="free" and active=true
**Validates: Requirements 1.3, 1.4, 1.5**

Property 7: Auth0 User ID Uniqueness
*For any* auth0_user_id that already exists in the users table, attempting to create a new account with that auth0_user_id should be rejected
**Validates: Requirements 1.3**

Property 8: Authentication via Auth0
*For any* user account with a stored auth0_user_id, authenticating through Auth0 should grant access to the system
**Validates: Requirements 1.6**

Property 9: Sheet Column Validation
*For any* Google Sheet, validation should pass if and only if all required columns (client_name, client_email, invoice_id, amount, currency, due_date, sent_date, status, last_stage_sent, last_sent_at) are present
**Validates: Requirements 3.2, 3.3**

Property 10: Sheet Validation Error Messages
*For any* Google Sheet missing required columns, the validation error should list the specific missing column names
**Validates: Requirements 3.4**

Property 11: Template Sheet Creation
*For any* user who chooses to create from template, the created Google Sheet should contain all required columns with correct headers
**Validates: Requirements 3.5**

Property 12: Sender Info Validation
*For any* sender information submission, both name and business_name must be non-empty strings, otherwise the submission should be rejected
**Validates: Requirements 4.2**

Property 13: Sender Info in Email Signatures
*For any* email draft created, the rendered template should contain both the user's name and business_name in the signature section
**Validates: Requirements 4.4, 8.3**

Property 14: Email Template Variable Substitution
*For any* email draft created, the rendered template should contain the invoice's client_name, invoice_id, amount, currency, and days_overdue
**Validates: Requirements 8.2**

Property 15: Stage-Specific Template Selection
*For any* escalation stage (7, 14, 21, 28, 35, 42), the email draft should use the template corresponding to that stage number
**Validates: Requirements 8.4**

Property 16: Draft Not Auto-Sent
*For any* email draft created, the Gmail API call should use the create_draft endpoint, not the send endpoint
**Validates: Requirements 8.6**

Property 17: Sheet Tracking Updates
*For any* invoice where a draft is created, the invoice row should be updated with last_stage_sent set to the current stage and last_sent_at set to the current date
**Validates: Requirements 9.1, 9.2**

Property 18: Status Filtering
*For any* invoice with status other than "Overdue" or "Open", the invoice should be skipped during processing
**Validates: Requirements 5.6**

Property 19: Upper Bound Stage Limit
*For any* invoice with days_overdue >= 42 and last_stage_sent = 42, no new draft should be created
**Validates: Requirements 5.5**

Property 20: Job History Record Creation
*For any* completed job run, a job history record should be created containing user_id, run_at timestamp, invoices_checked count, drafts_created count, and any errors that occurred
**Validates: Requirements 17.1, 17.2, 17.3, 5.7**

Property 21: Stripe Payment Success Updates Plan
*For any* successful Stripe payment webhook event, the corresponding user's plan should be updated to "paid"
**Validates: Requirements 12.3**

Property 22: Plan Upgrade Removes Limits
*For any* user whose plan changes from "free" to "paid", subsequent job runs should process all overdue invoices without the 3-invoice limit
**Validates: Requirements 11.3**

Property 23: Weekly Digest Content Completeness
*For any* weekly digest email generated, it should contain: drafts_created count for past 7 days, total outstanding amount, critical invoices count (35+ days), and a prompt to review Gmail drafts
**Validates: Requirements 13.2, 13.3, 13.4, 13.5**

Property 24: Free Tier Limit Upgrade Prompt
*For any* weekly digest where the user has plan="free" and reached the 3-invoice limit in the past week, the digest should include an upgrade prompt
**Validates: Requirements 10.4, 13.6**

Property 25: Consecutive Failure Notification
*For any* user with 3 consecutive failed job runs, an error notification email should be sent
**Validates: Requirements 14.1**

Property 26: Error Notification Content
*For any* error notification email, it should include the error type and suggested resolution steps
**Validates: Requirements 14.2**

Property 27: Onboarding Completion Activates Account
*For any* user who completes all onboarding steps (Google connection, sheet selection, sender info), the user's active flag should be set to true
**Validates: Requirements 16.4**

Property 28: Make.com Scenario Provisioning
*For any* user who completes Google connection, a Make.com scenario should be created/cloned and the scenario ID should be stored in the user account with configuration for sheet_id and sender info
**Validates: Requirements 19.1, 19.2, 19.3**

Property 29: Account Deactivation Pauses Scenario
*For any* user whose active flag is set to false, the associated Make.com scenario should be paused
**Validates: Requirements 19.4**

Property 30: Data Privacy - No Invoice Data Stored
*For any* state of the database, the users and job_history tables should not contain columns for invoice amounts, client names, or client emails
**Validates: Requirements 20.1, 20.3**

Property 31: OAuth Token Isolation
*For any* state of the database, there should be no Google OAuth tokens stored (all OAuth is handled by Make.com)
**Validates: Requirements 2.4, 20.4**

Property 32: Make.com Scenario Storage
*For any* successful Make.com OAuth callback, the scenario identifier should be stored in the user's make_scenario_id field
**Validates: Requirements 2.2**

Property 33: Sheet ID Persistence
*For any* sheet that passes validation, the sheet_id should be stored in the user's sheet_id field
**Validates: Requirements 3.6**

Property 34: Sender Info Persistence
*For any* valid sender information submission, the name and business_name should be stored in the user account
**Validates: Requirements 4.3**

## Error Handling

### Error Categories

1. **Google API Errors**:
   - Sheet access denied (OAuth token expired or revoked)
   - Sheet not found (deleted or moved)
   - Rate limiting (429 errors)
   - Network timeouts

2. **Make.com Errors**:
   - Scenario execution failure
   - API rate limits
   - Connection expiration
   - Scenario configuration errors

3. **Stripe Errors**:
   - Payment declined
   - Subscription cancellation
   - Webhook signature verification failure
   - Customer not found

4. **Application Errors**:
   - Database connection failures
   - Email delivery failures (SendGrid/Mailgun)
   - Invalid data in sheets (malformed emails, dates)
   - Concurrent job execution conflicts

### Error Handling Strategies

**Retry Logic**:
- Google API calls: 3 retries with exponential backoff (1s, 2s, 4s)
- Make.com API calls: 3 retries with exponential backoff
- Stripe API calls: Use Stripe SDK's built-in retry logic
- Email delivery: 2 retries with 5-second delay

**Graceful Degradation**:
- If sheet read fails: Log error, skip user for this run, send notification
- If draft creation fails for one invoice: Log error, continue with remaining invoices
- If sheet write fails: Log error, continue processing (draft still created)
- If job history write fails: Log to application logs, don't fail the job

**User Notifications**:
- 3 consecutive failures → Send error notification email
- OAuth token expired → Send re-authorization email with link
- Make.com connection lost → Send reconnection instructions
- Payment failed → Send payment update reminder

**Monitoring and Alerting**:
- Track job success rate per user (alert if < 90% over 7 days)
- Track overall system success rate (alert if < 95%)
- Monitor Stripe webhook delivery (alert on signature failures)
- Monitor email delivery rate (alert if < 98%)

### Error Response Formats

**API Error Response**:
```json
{
  "error": {
    "code": "SHEET_ACCESS_DENIED",
    "message": "Unable to access Google Sheet. Please reconnect your Google account.",
    "details": {
      "sheet_id": "abc123",
      "user_id": "uuid"
    },
    "resolution": "Visit /onboarding/connect-google to re-authorize"
  }
}
```

**Job Error Logging**:
```json
{
  "invoice_id": "INV-001",
  "error_type": "DRAFT_CREATION_FAILED",
  "error_message": "Gmail API returned 429: Rate limit exceeded",
  "timestamp": "2026-02-15T10:30:00Z",
  "retry_count": 3
}
```

## Testing Strategy

### Dual Testing Approach

This project requires both unit tests and property-based tests for comprehensive coverage:

**Unit Tests**: Focus on specific examples, edge cases, and integration points
- Specific API endpoint responses (signup, login, sheet selection)
- Stripe webhook handling for various event types
- Error notification email content
- Database migrations and schema validation
- Make.com API integration (mocked responses)

**Property-Based Tests**: Verify universal properties across all inputs
- Escalation logic (stage assignment, draft decision)
- Date calculations (days overdue, stage transitions)
- Billing state transitions (free → paid, limits)
- Sheet validation (various column configurations)
- Template rendering (variable substitution)

### Property-Based Testing Configuration

**Framework**: Use `hypothesis` for Python (FastAPI backend)

**Test Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with: `# Feature: smart-invoice, Property N: [property text]`
- Use custom strategies for domain objects (Invoice, User, dates)

**Example Property Test Structure**:
```python
from hypothesis import given, strategies as st
from datetime import date, timedelta

# Feature: smart-invoice, Property 2: Escalation Stage Assignment
@given(days_overdue=st.integers(min_value=0, max_value=100))
def test_stage_assignment_property(days_overdue):
    """
    For any number of days_overdue, the assigned escalation stage should be:
    None if < 7 days, 7 if 7-13 days, 14 if 14-20 days, etc.
    """
    stage = stage_for(days_overdue)
    
    if days_overdue < 7:
        assert stage is None
    elif 7 <= days_overdue < 14:
        assert stage == 7
    elif 14 <= days_overdue < 21:
        assert stage == 14
    elif 21 <= days_overdue < 28:
        assert stage == 21
    elif 28 <= days_overdue < 35:
        assert stage == 28
    elif 35 <= days_overdue < 42:
        assert stage == 35
    else:  # >= 42
        assert stage == 42
```

### Test Coverage Goals

- **Core Logic**: 100% coverage (escalation, draft decision, billing)
- **API Routes**: 90% coverage (all happy paths + major error cases)
- **Database Operations**: 95% coverage (CRUD + constraints)
- **Integration Points**: 80% coverage (Make.com, Stripe, email)

### Testing Priorities

**High Priority** (must test before MVP launch):
1. Escalation stage assignment (Property 2)
2. Draft creation decision logic (Property 3)
3. Free tier limits (Property 4)
4. Billing state transitions (Properties 21, 22)
5. Sheet validation (Properties 9, 10)
6. Data privacy constraints (Properties 30, 31)

**Medium Priority** (test during development):
7. Template rendering (Properties 13, 14, 15)
8. Job history logging (Property 20)
9. Error notifications (Properties 25, 26)
10. Account creation (Properties 6, 7, 8)

**Lower Priority** (can defer to post-MVP):
11. Weekly digest content (Properties 23, 24)
12. Make.com scenario management (Properties 28, 29)
13. UI/UX flows (examples only, not properties)

### Integration Testing

**Make.com Integration**:
- Use Make.com sandbox/test scenarios
- Mock Make.com API responses for unit tests
- Test scenario creation, configuration, and execution
- Verify webhook callbacks from Make.com

**Stripe Integration**:
- Use Stripe test mode
- Test webhook events with Stripe CLI
- Verify subscription creation and updates
- Test payment failure scenarios

**Google APIs** (via Make.com):
- Use test Google accounts
- Create test sheets with various data
- Verify OAuth flow (manual testing)
- Test sheet read/write operations

### Manual Testing Checklist

Before MVP launch, manually verify:
- [ ] Complete signup flow (< 2 minutes)
- [ ] Google OAuth connection (no warnings)
- [ ] Sheet selection and validation
- [ ] Template sheet creation
- [ ] Sender info submission
- [ ] Stripe checkout flow
- [ ] Payment success updates plan
- [ ] Free tier processes max 3 invoices
- [ ] Paid tier processes all invoices
- [ ] Gmail drafts appear correctly
- [ ] Sheet tracking updates correctly
- [ ] Weekly digest email received
- [ ] Error notification email received (simulate failure)
- [ ] Landing page displays correctly
- [ ] Onboarding confirmation message

## Deployment Architecture

### Hosting: Vercel (Serverless)

**Why Vercel**:
- Serverless functions (no server management)
- Automatic scaling
- Free tier sufficient for MVP
- Easy deployment from Git
- Built-in SSL/HTTPS
- No background job support needed (Make.com handles scheduling)

**Vercel Configuration** (`vercel.json`):
```json
{
  "version": 2,
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "main.py"
    },
    {
      "src": "/(.*)",
      "dest": "/static/$1"
    }
  ],
  "env": {
    "DATABASE_URL": "@database-url",
    "STRIPE_SECRET_KEY": "@stripe-secret-key",
    "STRIPE_WEBHOOK_SECRET": "@stripe-webhook-secret",
    "MAKE_API_KEY": "@make-api-key",
    "SENDGRID_API_KEY": "@sendgrid-api-key",
    "JWT_SECRET": "@jwt-secret"
  }
}
```

### Database: PostgreSQL (Managed)

**Options**:
- Vercel Postgres (easiest integration)
- Supabase (free tier, good for MVP)
- Railway (simple, affordable)
- Neon (serverless Postgres)

**Connection Pooling**:
- Use PgBouncer or built-in pooling
- Max connections: 20 (sufficient for serverless)

### Email Service

**Options**:
- SendGrid (free tier: 100 emails/day)
- Mailgun (free tier: 5,000 emails/month)
- Postmark (free tier: 100 emails/month)

**Recommendation**: SendGrid for MVP (generous free tier)

### Monitoring and Logging

**Application Logs**:
- Vercel built-in logging
- Log levels: ERROR, WARN, INFO
- Structured JSON logs

**Monitoring**:
- Vercel Analytics (free)
- Sentry for error tracking (free tier)
- Custom dashboard for job success rates

**Metrics to Track**:
- Job success rate per user
- Overall system success rate
- API response times
- Database query performance
- Email delivery rate
- Stripe webhook success rate

### Security

**Authentication**:
- Auth0 for user authentication (Universal Login)
- JWT tokens issued by Auth0
- Auth0 user profile stored in database

**API Security**:
- Rate limiting (100 requests/minute per IP)
- CORS configuration (whitelist frontend domain)
- Stripe webhook signature verification
- Make.com webhook authentication (API key)

**Data Security**:
- All connections over HTTPS
- Database credentials in environment variables
- No sensitive data in logs
- Regular security updates

**Privacy**:
- No invoice data stored (GDPR-friendly)
- User data encrypted at rest (database level)
- OAuth tokens managed by Make.com (not us)

### Backup and Recovery

**Database Backups**:
- Daily automated backups (managed service)
- 30-day retention
- Point-in-time recovery

**Disaster Recovery**:
- Database restore from backup
- Redeploy application from Git
- Reconfigure environment variables
- Notify users of downtime

**RTO/RPO**:
- Recovery Time Objective: 4 hours
- Recovery Point Objective: 24 hours (daily backups)

## Migration from CLI to SaaS

### Code Reuse Strategy

**Reuse Directly**:
- `router.py`: Escalation logic (`stage_for`, `should_send_draft`) → Port to Make.com custom functions
- `models.py`: Invoice and DraftCreated models → Use as Pydantic models in FastAPI
- Email templates: All 6 stage templates → Store in Make.com scenario

**Adapt for Web**:
- `config.py`: Settings → Environment variables in Vercel
- `scheduler.py`: Daily job logic → Implement in Make.com scenario
- `sheets.py`: Google Sheets operations → Use Make.com Google Sheets modules
- `emailer.py`: Gmail operations → Use Make.com Gmail modules

**Replace Completely**:
- CLI entry point (`main.py`) → FastAPI routes
- Local authentication → Web-based auth (JWT)
- Local config files → Database storage

### Migration Checklist

**Phase 1: Core Logic**:
- [ ] Port `stage_for()` to Make.com custom function
- [ ] Port `should_send_draft()` to Make.com router logic
- [ ] Port `days_overdue()` calculation
- [ ] Copy email templates to Make.com

**Phase 2: Web Backend**:
- [ ] Create FastAPI application structure
- [ ] Implement user authentication routes
- [ ] Implement onboarding routes
- [ ] Implement billing routes
- [ ] Implement job history webhook
- [ ] Implement weekly digest service

**Phase 3: Make.com Integration**:
- [ ] Create Make.com scenario template
- [ ] Implement scenario creation API
- [ ] Configure Google OAuth in Make.com
- [ ] Test scenario execution
- [ ] Implement webhook callback

**Phase 4: Frontend**:
- [ ] Create landing page
- [ ] Create signup form
- [ ] Create sheet selection UI
- [ ] Create sender info form
- [ ] Create confirmation page

**Phase 5: Testing**:
- [ ] Write property-based tests
- [ ] Write unit tests
- [ ] Perform integration testing
- [ ] Manual end-to-end testing

**Phase 6: Deployment**:
- [ ] Set up Vercel project
- [ ] Configure environment variables
- [ ] Set up PostgreSQL database
- [ ] Deploy to production
- [ ] Configure DNS
- [ ] Test production deployment

## Open Questions and Decisions

### Resolved

1. **Hosting**: Vercel (serverless, no background jobs needed)
2. **Database**: PostgreSQL (managed service)
3. **Email**: SendGrid (generous free tier)
4. **Auth**: Email/password + magic link (simple, no Google OAuth on our side)
5. **Make.com API**: Confirmed support for scenario creation and configuration

### To Be Resolved During Implementation

1. **Frontend Framework**: Static HTML + Alpine.js or htmx (decision: use static HTML with Alpine.js or htmx, NOT React — landing page + 4-step onboarding doesn't justify SPA overhead)
2. **Database Provider**: Vercel Postgres vs Supabase vs Railway (decision: evaluate during setup)
3. **Weekly Digest Trigger**: External cron service (cron-job.org) vs Vercel Cron (decision: test both)
4. **Magic Link vs Password**: Support both or choose one (decision: support both for flexibility)
5. **Make.com Scenario Template**: Build from scratch vs adapt existing blueprint (decision: build from scratch for full control)

## Success Criteria

The MVP is successful if:

1. **Functional**: User can sign up, connect Google, select sheet, and receive Gmail drafts
2. **Reliable**: 99%+ job success rate over 7 days
3. **Fast**: Signup flow completes in < 2 minutes
4. **Secure**: No security vulnerabilities in auth or payment flow
5. **Revenue**: At least 1 paying customer ($5 revenue)
6. **Learning**: Clear understanding of what users want and what they'll pay for

## Next Steps

After design approval:
1. Create implementation task list (tasks.md)
2. Set up development environment
3. Begin Phase 1: Core Logic migration
4. Iterate through phases 2-6
5. Deploy MVP
6. Launch distribution campaign (2 days)
7. Measure and learn
