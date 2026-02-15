# Requirements Document: Smart Invoice SaaS MVP

## Introduction

Smart Invoice is a hosted SaaS application that automates invoice follow-up for small businesses. The system enables non-technical users to connect their Google account through Make.com, select their invoice spreadsheet, and receive automated Gmail draft reminders for overdue invoices following a 6-stage escalation schedule over 42 days. The system provides weekly digest emails to demonstrate value and supports both free (3 invoices) and paid ($15/month) tiers via Stripe.

This MVP transforms an existing Python CLI tool (7 source files, 41 tests) into a hosted web service with zero-friction onboarding, targeting small business owners who use Google Workspace and need automated payment follow-up without technical complexity.

## Glossary

- **System**: The Smart Invoice SaaS application (web app + Make.com automation)
- **User**: A small business owner who signs up for the service
- **Make_Scenario**: A Make.com automation workflow that runs daily for a specific user
- **Invoice_Sheet**: A Google Sheet containing invoice data with required columns
- **Escalation_Stage**: One of six reminder levels (7, 14, 21, 28, 35, 42 days overdue)
- **Gmail_Draft**: An email draft created in the user's Gmail account (not auto-sent)
- **Weekly_Digest**: A summary email sent every Monday showing system activity
- **Free_Tier**: Service plan limited to 3 overdue invoices per daily run
- **Paid_Tier**: Service plan with unlimited invoices at $15/month
- **Overdue_Invoice**: An invoice where current date exceeds due date
- **Template_Sheet**: A pre-configured Google Sheet with required column structure
- **Job_Run**: A single execution of the daily processing for one user
- **Sender_Info**: User's name and business name used in email signatures

## Requirements

### Requirement 1: User Account Management

**User Story:** As a small business owner, I want to create an account using Auth0 (managed authentication), so that I can securely access the invoice follow-up service without the system implementing homebrew security.

#### Acceptance Criteria

1. WHEN a user initiates signup, THE System SHALL redirect to Auth0 Universal Login (email/password or magic link)
2. WHEN Auth0 authentication succeeds, THE System SHALL receive user profile information
3. WHEN a new user authenticates for the first time, THE System SHALL create a user record in the database
4. THE System SHALL store user email, name (from Auth0 profile), business name, and account creation timestamp
5. WHEN a user account is created, THE System SHALL set the default plan to Free_Tier
6. WHEN a returning user authenticates, THE System SHALL retrieve their existing user record
7. THE System SHALL NOT implement custom JWT or homebrew authentication (Auth0 is non-negotiable for security)

### Requirement 2: Google Account Connection via Make.com

**User Story:** As a user, I want to connect my Google account through Make.com's verified OAuth, so that the system can access my Google Sheets and Gmail without security warnings.

#### Acceptance Criteria

1. WHEN a user initiates Google connection, THE System SHALL redirect to Make.com's verified OAuth flow
2. WHEN Make.com OAuth completes successfully, THE System SHALL receive and store the Make_Scenario identifier
3. THE System SHALL request only gmail.compose and spreadsheets scopes through Make.com
4. THE System SHALL NOT store or handle Google OAuth tokens directly
5. WHEN Google connection fails, THE System SHALL display an error message and allow retry
6. WHEN a Make_Scenario is cloned, THE System SHALL set the user_id as a build variable in the scenario
7. THE Make_Scenario SHALL remain stateless, storing only the user_id build variable

### Requirement 3: Invoice Sheet Selection and Validation

**User Story:** As a user, I want to select my existing Google Sheet or create one from a template, so that the system knows which invoices to track.

#### Acceptance Criteria

1. WHEN a user completes Google connection, THE System SHALL display a list of the user's Google Sheets
2. WHEN a user selects a sheet, THE System SHALL validate that required columns exist
3. THE System SHALL require these columns: client_name, client_email, invoice_id, amount, currency, due_date, sent_date, status, last_stage_sent, last_sent_at
4. WHEN required columns are missing, THE System SHALL display an error with column names and provide a link to Template_Sheet
5. WHEN a user chooses to create from template, THE System SHALL create a new Google Sheet with required columns pre-configured
6. WHEN sheet validation passes, THE System SHALL store the sheet_id in the user account

### Requirement 4: Sender Information Collection

**User Story:** As a user, I want to provide my name and business name during setup, so that email signatures are personalized with my information.

#### Acceptance Criteria

1. WHEN a user completes sheet selection, THE System SHALL prompt for name and business_name
2. THE System SHALL require both name and business_name fields to be non-empty
3. WHEN sender information is submitted, THE System SHALL store it in the user account
4. THE System SHALL use Sender_Info in all email template signatures

### Requirement 5: Daily Invoice Processing via Make.com

**User Story:** As a user, I want the system to automatically check my invoices daily and create reminder drafts, so that I don't have to manually track overdue payments.

#### Acceptance Criteria

1. THE Make_Scenario SHALL execute once per day for each active user
2. WHEN a Job_Run starts, THE Make_Scenario SHALL call GET /api/users/{user_id}/config to fetch sheet_id, sender_name, business_name, plan, and invoice_limit
3. THE Make_Scenario SHALL read rows from the user's Invoice_Sheet using the sheet_id from the config API
4. FOR each invoice row, THE Make_Scenario SHALL calculate days overdue as (current_date - due_date)
5. WHEN an invoice has days_overdue >= 7, THE Make_Scenario SHALL determine the appropriate Escalation_Stage
6. WHEN an invoice has days_overdue >= 42, THE Make_Scenario SHALL NOT create additional drafts
7. THE Make_Scenario SHALL process only invoices with status "Overdue" or "Open"
8. WHEN a Job_Run completes, THE Make_Scenario SHALL POST results to /api/webhooks/make-results with user_id, drafts_created, and total_outstanding_amount
9. THE System SHALL record execution timestamp, invoices_checked count, and drafts_created count in job history

### Requirement 6: Escalation Stage Determination

**User Story:** As a user, I want the system to send progressively urgent reminders based on how long an invoice is overdue, so that clients receive appropriate follow-up.

#### Acceptance Criteria

1. WHEN days_overdue is 7-13, THE System SHALL assign Escalation_Stage 7
2. WHEN days_overdue is 14-20, THE System SHALL assign Escalation_Stage 14
3. WHEN days_overdue is 21-27, THE System SHALL assign Escalation_Stage 21
4. WHEN days_overdue is 28-34, THE System SHALL assign Escalation_Stage 28
5. WHEN days_overdue is 35-41, THE System SHALL assign Escalation_Stage 35
6. WHEN days_overdue is 42 or more, THE System SHALL assign Escalation_Stage 42
7. WHEN days_overdue is less than 7, THE System SHALL NOT assign any Escalation_Stage

### Requirement 7: Draft Creation Logic

**User Story:** As a user, I want the system to create Gmail drafts only when appropriate, so that I don't receive duplicate reminders or skip stages.

#### Acceptance Criteria

1. WHEN an invoice has no last_stage_sent value, THE System SHALL create a Gmail_Draft for the current Escalation_Stage
2. WHEN an invoice's current Escalation_Stage is greater than last_stage_sent, THE System SHALL create a Gmail_Draft
3. WHEN an invoice's last_sent_at equals current date, THE System SHALL NOT create a Gmail_Draft
4. WHEN an invoice's current Escalation_Stage equals last_stage_sent, THE System SHALL NOT create a Gmail_Draft
5. WHEN an invoice's current Escalation_Stage is less than last_stage_sent, THE System SHALL NOT create a Gmail_Draft

### Requirement 8: Gmail Draft Content

**User Story:** As a user, I want Gmail drafts to contain personalized invoice details and my business signature, so that clients receive professional reminders.

#### Acceptance Criteria

1. THE System SHALL use the user's Gmail address as the sender for all Gmail_Drafts
2. WHEN creating a Gmail_Draft, THE System SHALL populate the template with client_name, invoice_id, amount, currency, and days_overdue
3. THE System SHALL include Sender_Info (name and business_name) in the email signature
4. THE System SHALL use stage-specific email templates corresponding to the Escalation_Stage
5. THE Gmail_Draft SHALL appear in the user's Gmail Drafts folder
6. THE Gmail_Draft SHALL NOT be automatically sent

### Requirement 9: Sheet Tracking Updates

**User Story:** As a user, I want the system to record which reminders were sent in my spreadsheet, so that I can track follow-up history.

#### Acceptance Criteria

1. WHEN a Gmail_Draft is created, THE System SHALL update the invoice row's last_stage_sent to the current Escalation_Stage
2. WHEN a Gmail_Draft is created, THE System SHALL update the invoice row's last_sent_at to the current date
3. THE System SHALL write updates back to the Invoice_Sheet within the same Job_Run
4. WHEN sheet write fails, THE System SHALL log the error and continue processing remaining invoices

### Requirement 10: Free Tier Limits

**User Story:** As a free tier user, I want to process up to 3 overdue invoices per day, so that I can evaluate the service before paying.

#### Acceptance Criteria

1. WHEN a user has plan set to Free_Tier, THE System SHALL return invoice_limit=3 from GET /api/users/{user_id}/config
2. WHEN a user has plan set to Paid_Tier, THE System SHALL return invoice_limit=100 from GET /api/users/{user_id}/config
3. THE Make_Scenario SHALL use the invoice_limit value to cap the Google Sheets "Search Rows" module limit field
4. WHEN Free_Tier limit is reached, THE System SHALL skip remaining Overdue_Invoices
5. WHEN Free_Tier limit is reached, THE System SHALL include an upgrade prompt in the Weekly_Digest

### Requirement 11: Paid Tier Processing

**User Story:** As a paid subscriber, I want unlimited invoice processing, so that all my overdue invoices receive automated follow-up.

#### Acceptance Criteria

1. WHEN a user has plan set to Paid_Tier, THE System SHALL process all Overdue_Invoices without limit
2. THE Paid_Tier SHALL cost $15 per month
3. WHEN a user upgrades from Free_Tier to Paid_Tier, THE System SHALL immediately remove processing limits

### Requirement 12: Stripe Payment Integration

**User Story:** As a user, I want to pay for the service via Stripe, so that I can unlock unlimited invoice processing.

#### Acceptance Criteria

1. WHEN a user initiates upgrade, THE System SHALL redirect to Stripe Checkout
2. THE System SHALL create a Stripe subscription for $15/month
3. WHEN Stripe payment succeeds, THE System SHALL update the user's plan to Paid_Tier
4. WHEN Stripe payment fails, THE System SHALL keep the user on Free_Tier and display an error
5. THE System SHALL handle Stripe webhook events for subscription status changes

### Requirement 13: Weekly Digest Email

**User Story:** As a user, I want to receive a weekly summary of system activity, so that I know the service is working and see the value it provides.

#### Acceptance Criteria

1. THE System SHALL send a Weekly_Digest email to each active user every Monday
2. THE Weekly_Digest SHALL include the count of drafts created in the past 7 days (from job_history)
3. THE Weekly_Digest SHALL include the total outstanding amount across all Overdue_Invoices (from webhook data)
4. THE Weekly_Digest SHALL include the count of critical invoices (35+ days overdue) calculated from webhook data
5. THE Weekly_Digest SHALL include a prompt to review Gmail drafts
6. WHEN a Free_Tier user has reached their limit, THE Weekly_Digest SHALL include an upgrade prompt

### Requirement 14: Error Notification

**User Story:** As a user, I want to be notified when something goes wrong with my automation, so that I can fix issues promptly.

#### Acceptance Criteria

1. WHEN a Job_Run fails 3 consecutive times for a user, THE System SHALL send an error notification email
2. THE error notification SHALL include the error type and suggested resolution steps
3. WHEN Google Sheet access is lost, THE System SHALL send an error notification with re-authorization instructions
4. WHEN Make.com connection expires, THE System SHALL send an error notification with reconnection instructions

### Requirement 15: Landing Page and Signup Flow

**User Story:** As a prospective user, I want a simple landing page with clear value proposition, so that I can quickly understand and sign up for the service.

#### Acceptance Criteria

1. THE System SHALL display a landing page with headline, 3-bullet value proposition, and signup button
2. THE landing page SHALL display pricing information for Free_Tier and Paid_Tier
3. WHEN a user clicks signup, THE System SHALL display the account creation form
4. THE signup flow SHALL complete in under 2 minutes for a typical user
5. THE landing page SHALL include social proof (case study results)

### Requirement 16: Onboarding Completion

**User Story:** As a new user, I want clear confirmation after setup, so that I know the system is configured correctly.

#### Acceptance Criteria

1. WHEN onboarding completes successfully, THE System SHALL display a confirmation message
2. THE confirmation message SHALL state that Gmail_Drafts will be created for overdue invoices
3. THE confirmation message SHALL state that Weekly_Digest emails will arrive every Monday
4. THE System SHALL mark the user account as active after successful onboarding

### Requirement 17: Job History Logging

**User Story:** As a system administrator, I want detailed logs of all job executions, so that I can monitor reliability and debug issues.

#### Acceptance Criteria

1. WHEN a Job_Run completes, THE System SHALL create a job history record
2. THE job history record SHALL include user_id, run_at timestamp, invoices_checked count, and drafts_created count
3. WHEN errors occur during a Job_Run, THE System SHALL store error details in the job history record
4. THE System SHALL retain job history records for at least 90 days

### Requirement 18: Email Template Content

**User Story:** As a user, I want email templates to follow a proven escalation sequence, so that my follow-up is professional and effective.

#### Acceptance Criteria

1. THE Stage 7 template SHALL use a friendly check-in tone
2. THE Stage 14 template SHALL use a direct follow-up tone
3. THE Stage 21 template SHALL use an urgent tone
4. THE Stage 28 template SHALL use a firm tone and suggest scheduling a call
5. THE Stage 35 template SHALL use a final warning tone before escalation
6. THE Stage 42 template SHALL use a last notice tone and mention next steps

### Requirement 19: Make.com Scenario Management

**User Story:** As a system administrator, I want each user to have their own Make.com scenario, so that processing is isolated and scalable.

#### Acceptance Criteria

1. WHEN a user completes Google connection, THE System SHALL create or clone a Make_Scenario for that user
2. THE System SHALL store the Make_Scenario identifier in the user account
3. THE Make_Scenario SHALL be configured with only the user_id as a build variable (stateless design)
4. WHEN a user deactivates their account, THE System SHALL pause the associated Make_Scenario

### Requirement 21: User Config API Endpoint

**User Story:** As a Make.com scenario, I need to fetch user configuration at the start of each run, so that I can process invoices with current user data and plan limits.

#### Acceptance Criteria

1. THE System SHALL provide a GET /api/users/{user_id}/config endpoint
2. WHEN the endpoint is called with a valid user_id, THE System SHALL return sheet_id, sender_name, business_name, plan, and invoice_limit
3. THE invoice_limit SHALL be 3 for Free_Tier users and 100 for Paid_Tier users
4. WHEN the user_id is invalid or user is inactive, THE System SHALL return a 404 error
5. THE endpoint SHALL require authentication via API key from Make.com

### Requirement 22: Make.com Results Webhook

**User Story:** As a Make.com scenario, I need to report job execution results back to the backend, so that the system can track activity and generate weekly digests.

#### Acceptance Criteria

1. THE System SHALL provide a POST /api/webhooks/make-results endpoint
2. WHEN the endpoint receives a webhook, THE System SHALL accept user_id, drafts_created, total_outstanding_amount, and critical_invoices_count
3. THE System SHALL create a job_history record with the provided data
4. THE System SHALL update the user's last_run_at timestamp
5. THE endpoint SHALL require authentication via API key from Make.com
6. WHEN webhook data is invalid, THE System SHALL return a 400 error with details

### Requirement 20: Data Privacy

**User Story:** As a user, I want my invoice data to remain in my Google Sheet, so that my financial information stays private.

#### Acceptance Criteria

1. THE System SHALL NOT store invoice amounts, client names, or client emails in its database
2. THE System SHALL read invoice data only during Job_Run execution
3. THE System SHALL store only user account information, Make_Scenario identifiers, and job execution metadata
4. THE System SHALL access Google Sheets and Gmail only through Make.com's OAuth tokens
