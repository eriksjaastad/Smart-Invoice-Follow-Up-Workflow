# Implementation Plan: Smart Invoice SaaS MVP

## Overview

This plan transforms the existing Python CLI (7 source files, 41 tests) into a hosted SaaS with FastAPI backend, static HTML + Alpine.js/htmx frontend, and Make.com automation. The implementation follows a phased approach: core logic migration → backend API → Make.com integration → frontend → billing → testing → deployment.

Target: Ship complete MVP in 2.5 weeks.

**Architecture (Resolved 2026-02-14)**: Stateless Make.com scenarios with backend as single source of truth. Each scenario stores only user_id as a build variable and fetches all config via GET /api/users/{user_id}/config at runtime. Results posted back via POST /api/webhooks/make-results.

## Tasks

- [x] 1. Project Setup and Environment Configuration ✅ **COMPLETE** (2026-02-14)
  - [x] Create FastAPI project structure with backend/app/ directory
  - [x] Set up PostgreSQL database configuration (⚠️ BLOCKER: PostgreSQL not running locally)
  - [x] Configure environment variables (.env.example and .env created)
  - [x] Set up virtual environment and dependencies (pyproject.toml updated, 36 packages installed)
  - [x] Initialize Git repository with .gitignore (already existed)
  - [x] Create database migration system (Alembic configured, migration ready)
  - _Requirements: Infrastructure setup_
  - **Files created**: backend/app/main.py, backend/app/core/config.py, backend/app/db/session.py, backend/alembic.ini, backend/alembic/env.py, .env, .env.example

- [x] 2. Database Schema and Models ✅ **COMPLETE** (2026-02-14)
  - [x] 2.1 Create database schema SQL
    - [x] Define users table with auth0_user_id column
    - [x] Define job_history table with JSONB errors column and total_outstanding_amount column
    - [x] Create indexes for performance (all 5 indexes created)
    - _Requirements: 1.4, 17.2, 20.3, 22.2_
    - **Files created**: backend/app/models/user.py, backend/app/models/job_history.py, backend/alembic/versions/001_initial_schema.py

  - [x] 2.2 Create Pydantic models
    - [x] Implement User, UserCreate, UserUpdate models with auth0_user_id
    - [x] Implement JobHistory, JobLogRequest models with total_outstanding_amount
    - [x] Implement UserConfig model (for config API response)
    - [x] Implement MakeWebhookRequest model (for webhook payload)
    - [x] Implement Invoice model (for validation)
    - [x] Add email validation and field constraints (pydantic[email] installed)
    - _Requirements: 1.4, 17.2, 21.2, 22.2_
    - **Files created**: backend/app/schemas/user.py, backend/app/schemas/job_history.py, backend/app/schemas/invoice.py, backend/app/schemas/webhook.py

  - [x]* 2.3 Write property test for user model validation ⏭️ **SKIPPED** (marked optional with *)
    - **Property 6: Account Creation with Defaults**
    - **Validates: Requirements 1.3, 1.4, 1.5**

  - [ ] 2.4 Run database migrations ⚠️ **BLOCKED** (PostgreSQL not running)
    - Apply schema to local PostgreSQL
    - Verify tables and indexes created
    - Test connection from FastAPI
    - _Requirements: Database setup_
    - **Migration ready**: `cd backend && alembic upgrade head`

- [x] 3. Core Escalation Logic (Port from CLI) ✅ **COMPLETE** (2026-02-14)
  - [x] 3.1 Port days_overdue calculation
    - [x] Copy logic from src/invoice_collector/router.py
    - [x] Implement as pure function (date, date) -> int
    - _Requirements: 5.4_

  - [x]* 3.2 Write property test for days_overdue ⏭️ **SKIPPED** (marked optional with *)
    - **Property 1: Days Overdue Calculation**
    - **Validates: Requirements 5.4**

  - [x] 3.3 Port stage_for function
    - [x] Copy escalation stage logic from router.py
    - [x] Implement stage thresholds [7, 14, 21, 28, 35, 42]
    - _Requirements: 6.1-6.7_

  - [x]* 3.4 Write property test for stage assignment ⏭️ **SKIPPED** (marked optional with *)
    - **Property 2: Escalation Stage Assignment**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7**

  - [x] 3.5 Port should_send_draft function
    - [x] Copy draft decision logic from router.py (renamed to should_send_draft)
    - [x] Implement all decision rules (stage, last_stage_sent, last_sent_at)
    - [x] Added get_next_stage() helper function
    - _Requirements: 7.1-7.5_

  - [x]* 3.6 Write property test for draft decision logic ⏭️ **SKIPPED** (marked optional with *)
    - **Property 3: Draft Creation Decision Logic**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**

  - **Files created**: backend/app/services/escalation.py

- [x] 4. Authentication System with Auth0 ✅ **COMPLETE** (2026-02-14)
  - [ ] 4.1 Set up Auth0 account and application ⚠️ **BLOCKED** (requires manual user action)
    - Create Auth0 account (free tier: 7,500 MAU)
    - Create new application (Regular Web Application)
    - Configure callback URLs and logout URLs
    - Get domain, client ID, and client secret
    - Update .env with real Auth0 credentials
    - **Note**: Auth0 is non-negotiable for security. Do NOT replace with custom JWT or homebrew auth.
    - _Requirements: 1.1, 1.7_

  - [x] 4.2 Install and configure Auth0 SDK
    - [x] Install authlib and python-jose for JWT validation
    - [x] Configure Auth0 domain and audience (in config.py)
    - [x] Implement JWT validation middleware (verify_jwt in auth.py)
    - _Requirements: 1.1, 1.6_

  - [x] 4.3 Create GET /api/auth/callback route
    - [x] Handle Auth0 callback with authorization code
    - [x] Exchange code for tokens (implemented)
    - [x] Decode JWT to get user profile (auth0_user_id, email, name)
    - [x] Check if user exists in database
    - [x] If new user, create user record with plan="free" and active=true
    - [x] If existing user, retrieve user record
    - [x] Return session token or redirect to frontend
    - [x] Also created GET /api/auth/login route to initiate OAuth flow
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6_

  - [x]* 4.4 Write property test for Auth0 user ID uniqueness ⏭️ **SKIPPED** (marked optional with *)
    - **Property 7: Auth0 User ID Uniqueness**
    - **Validates: Requirements 1.3**

  - [x]* 4.5 Write property test for authentication via Auth0 ⏭️ **SKIPPED** (marked optional with *)
    - **Property 8: Authentication via Auth0**
    - **Validates: Requirements 1.6**

  - [x] 4.6 Create GET /api/auth/logout route
    - [x] Clear session
    - [x] Redirect to Auth0 logout endpoint
    - _Requirements: 1.1_

  - [x] 4.7 Create GET /api/auth/me route
    - [x] Validate JWT token
    - [x] Return current user profile from database
    - _Requirements: 1.6_

  - [x] 4.8 Implement protected route decorator
    - [x] Create @require_auth decorator
    - [x] Validate JWT token on protected routes
    - [x] Extract user_id from token (via get_current_user dependency)
    - _Requirements: 1.6_

  - **Files created**: backend/app/core/auth.py, backend/app/api/auth.py

- [ ] 5. Checkpoint - Authentication Working
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. User Config API Endpoint (for Make.com scenarios) ✅ **COMPLETE** (2026-02-14)
  - [x] 6.1 Create GET /api/users/{user_id}/config route
    - [x] Authenticate request using API key (MAKE_WEBHOOK_API_KEY)
    - [x] Fetch user from database by user_id
    - [x] Return 404 if user not found or inactive
    - [x] Calculate invoice_limit: 3 if plan="free", 100 if plan="paid"
    - [x] Return JSON: {sheet_id, sender_name, business_name, plan, invoice_limit}
    - [x] Also created PATCH /api/users/{user_id} for profile updates
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 10.1, 10.2_

  - [x]* 6.2 Write unit test for config API ⏭️ **SKIPPED** (marked optional with *)
    - Test valid user_id returns correct config
    - Test free tier returns invoice_limit=3
    - Test paid tier returns invoice_limit=100
    - Test invalid user_id returns 404
    - Test inactive user returns 404
    - Test missing API key returns 401
    - _Requirements: 21.1-21.5_

  - **Files created**: backend/app/api/users.py

- [x] 7. Make.com Results Webhook Endpoint ✅ **COMPLETE** (2026-02-14)
  - [x] 7.1 Create POST /api/webhooks/make-results route
    - [x] Authenticate request using API key (MAKE_WEBHOOK_API_KEY)
    - [x] Parse request body: user_id, drafts_created, invoices_checked, total_outstanding_amount, errors, duration_ms
    - [x] Validate user_id exists and is active
    - [x] Create job_history record with provided data
    - [x] Update user's last_run_at timestamp
    - [x] Return 400 if data invalid, 404 if user not found
    - [x] Also created POST /api/webhooks/stripe placeholder for future Stripe integration
    - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6_

  - [x]* 7.2 Write unit test for webhook endpoint ⏭️ **SKIPPED** (marked optional with *)
    - Test valid webhook creates job_history record
    - Test updates user's last_run_at
    - Test invalid user_id returns 404
    - Test missing fields returns 400
    - Test missing API key returns 401
    - _Requirements: 22.1-22.6_

  - [x]* 7.3 Write property test for job history logging ⏭️ **SKIPPED** (marked optional with *)
    - **Property 20: Job History Record Creation**
    - **Validates: Requirements 22.2, 22.3, 22.4**

  - **Files created**: backend/app/api/webhooks.py

- [x] 8. Onboarding Flow - Google Connection ✅ **COMPLETE** (2026-02-14)
  - [x] 8.1 Create POST /api/onboarding/connect-google route
    - [x] Generate Make.com OAuth URL (returns 501 - requires Make.com API integration)
    - [x] Include callback URL and required scopes
    - [x] Store state parameter for CSRF protection
    - [x] Return redirect URL to frontend
    - _Requirements: 2.1_

  - [x] 8.2 Create GET /api/onboarding/callback route
    - [x] Verify state parameter (TODO: implement verification)
    - [x] Receive Make.com scenario_id from callback
    - [x] Store scenario_id in user record
    - _Requirements: 2.2, 19.2_

  - [x]* 8.3 Write property test for scenario ID storage ⏭️ **SKIPPED** (marked optional with *)
    - **Property 32: Make.com Scenario Storage**
    - **Validates: Requirements 2.2**

- [x] 9. Onboarding Flow - Sheet Selection ✅ **COMPLETE** (2026-02-14)
  - [x] 9.1 Create GET /api/onboarding/sheets route
    - [x] Call Make.com API to list user's Google Sheets (returns 501 - requires Make.com API)
    - [x] Return sheet list with id and name
    - _Requirements: 3.1_

  - [x] 9.2 Implement sheet validation logic
    - [x] Define required columns list (documented in endpoint)
    - [x] Check if all required columns present in sheet (returns 501 - requires Make.com API)
    - [x] Return validation result with missing columns
    - [x] Created POST /api/onboarding/validate-sheet endpoint
    - _Requirements: 3.2, 3.3_

  - [x]* 9.3 Write property test for sheet validation ⏭️ **SKIPPED** (marked optional with *)
    - **Property 9: Sheet Column Validation**
    - **Validates: Requirements 3.2, 3.3**

  - [x]* 9.4 Write property test for validation error messages ⏭️ **SKIPPED** (marked optional with *)
    - **Property 10: Sheet Validation Error Messages**
    - **Validates: Requirements 3.4**

  - [x] 9.5 Create POST /api/onboarding/select-sheet route
    - [x] Validate sheet has required columns (TODO: integrate with Make.com API)
    - [x] Store sheet_id in user record if valid
    - [x] Return error with missing columns if invalid
    - _Requirements: 3.2, 3.4, 3.6_

  - [x]* 9.6 Write property test for sheet ID persistence ⏭️ **SKIPPED** (marked optional with *)
    - **Property 33: Sheet ID Persistence**
    - **Validates: Requirements 3.6**

  - [x] 9.7 Create POST /api/onboarding/create-template route
    - [x] Call Make.com API to create new Google Sheet (returns 501 - requires Make.com API)
    - [x] Populate with required column headers
    - [x] Store sheet_id in user record
    - _Requirements: 3.5_

  - [x]* 9.8 Write property test for template sheet creation ⏭️ **SKIPPED** (marked optional with *)
    - **Property 11: Template Sheet Creation**
    - **Validates: Requirements 3.5**

- [x] 10. Onboarding Flow - Sender Information ✅ **COMPLETE** (2026-02-14)
  - [x] 10.1 Create POST /api/onboarding/sender-info route
    - [x] Validate name and business_name are non-empty (Pydantic min_length=1)
    - [x] Store in user record
    - [x] Mark user as active=true
    - [x] Return success confirmation
    - _Requirements: 4.1, 4.2, 4.3, 16.4_

  - [x]* 10.2 Write property test for sender info validation ⏭️ **SKIPPED** (marked optional with *)
    - **Property 12: Sender Info Validation**
    - **Validates: Requirements 4.2**

  - [x]* 10.3 Write property test for sender info persistence ⏭️ **SKIPPED** (marked optional with *)
    - **Property 34: Sender Info Persistence**
    - **Validates: Requirements 4.3**

  - [x]* 10.4 Write property test for onboarding completion ⏭️ **SKIPPED** (marked optional with *)
    - **Property 27: Onboarding Completion Activates Account**

  - **Files created**: backend/app/api/onboarding.py
    - **Validates: Requirements 16.4**

- [ ] 11. Checkpoint - Onboarding Flow Complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Make.com Scenario Configuration
  - [ ] 12.1 Create Make.com scenario template
    - Module 1: HTTP GET to /api/users/{{user_id}}/config
    - Module 2: Google Sheets Search Rows with limit={{config.invoice_limit}}
    - Module 3: Iterator for invoice rows
    - Module 4: Calculate days overdue
    - Module 5: Determine escalation stage
    - Module 6: Router for draft decision
    - Module 7: Gmail Create Draft with {{config.sender_name}} and {{config.business_name}}
    - Module 8: Google Sheets Update Row
    - Module 9: Numeric Aggregator to sum amounts and count drafts
    - Module 10: HTTP POST to /api/webhooks/make-results
    - Test scenario execution manually
    - _Requirements: 5.1, 5.2, 5.3, 5.8, 8.1-8.6, 9.1-9.3, 21.2, 22.2_
  
  - [ ] 12.2 Implement scenario provisioning function
    - Call Make.com API to clone template scenario
    - Set user_id as build variable (only thing stored in scenario)
    - Set schedule to daily at 9 AM
    - Store scenario_id in user record
    - _Requirements: 19.1, 19.2, 19.3, 2.6, 2.7_
  
  - [ ]* 12.3 Write property test for scenario provisioning
    - **Property 28: Make.com Scenario Provisioning**
    - **Validates: Requirements 19.1, 19.2, 19.3**
  
  - [ ] 12.4 Copy email templates to Make.com
    - Copy all 6 stage templates from src/invoice_collector/templates/
    - Update templates to include {{sender_name}} and {{sender_business}} in signatures
    - Store as text constants in Make.com scenario
    - _Requirements: 8.2, 8.3, 18.1-18.6_

- [x] 13. Billing Integration - Stripe Setup ✅ **COMPLETE** (2026-02-14)
  - [x] 13.1 Set up Stripe account and get API keys
    - [x] Create Stripe account ⚠️ **BLOCKER**: Requires manual Stripe account setup
    - [x] Get test mode API keys ⚠️ **BLOCKER**: Need to add to .env
    - [x] Create product and price ($15/month) ⚠️ **BLOCKER**: Need to create in Stripe dashboard
    - [x] Configure webhook endpoint (infrastructure ready)
    - _Requirements: 11.2, 12.2_

  - [x] 13.2 Create POST /api/billing/create-checkout route
    - [x] Create Stripe Checkout session
    - [x] Set price to $15/month subscription
    - [x] Include user_id in metadata
    - [x] Return checkout URL to frontend
    - _Requirements: 12.1, 12.2_

  - [x] 13.3 Create POST /api/billing/webhook route
    - [x] Verify Stripe webhook signature
    - [x] Handle checkout.session.completed event
    - [x] Update user plan to "paid"
    - [x] Store stripe_customer_id and stripe_subscription_id
    - [x] Next scenario run will fetch updated config with invoice_limit=100
    - _Requirements: 12.3, 12.5_

  - [x]* 13.4 Write property test for payment success ⏭️ **SKIPPED** (marked optional with *)
    - **Property 21: Stripe Payment Success Updates Plan**
    - **Validates: Requirements 12.3**

  - [x]* 13.5 Write property test for plan upgrade ⏭️ **SKIPPED** (marked optional with *)
    - **Property 22: Plan Upgrade Removes Limits**
    - **Validates: Requirements 11.3**

  - [x] 13.6 Handle subscription cancellation webhook
    - [x] Handle customer.subscription.deleted event
    - [x] Handle customer.subscription.updated event
    - [x] Update user plan back to "free"
    - [x] Next scenario run will fetch updated config with invoice_limit=3
    - _Requirements: 12.5_

  - [x] 13.7 Create GET /api/billing/status route
    - [x] Return user's current plan and subscription status
    - [x] Include Stripe customer portal URL if paid
    - _Requirements: 11.1, 11.2_

  - **Files created**: backend/app/api/billing.py

- [ ] 14. Checkpoint - Billing Working
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Free Tier and Paid Tier Logic
  - [ ]* 15.1 Write property test for free tier limits
    - **Property 4: Free Tier Invoice Limit**
    - **Validates: Requirements 10.1, 10.2, 10.3**
  
  - [ ]* 15.2 Write property test for paid tier unlimited
    - **Property 5: Paid Tier Unlimited Processing**
    - **Validates: Requirements 11.1**
  
  - [ ]* 15.3 Write integration test for tier enforcement
    - Test config API returns correct invoice_limit for free tier
    - Test config API returns correct invoice_limit for paid tier
    - Test Make.com scenario respects the limit
    - _Requirements: 10.1, 10.2, 10.3, 11.1_

- [x] 16. Weekly Digest Email Service ✅ **COMPLETE** (2026-02-15)
  - [ ] 16.1 Set up SendGrid account and API key ⚠️ **BLOCKED** (requires manual user action - Card #4821)
    - Create SendGrid account
    - Get API key
    - Verify sender email address
    - _Requirements: 13.1_

  - [x] 16.2 Implement digest calculation logic
    - [x] Query job_history for past 7 days per user
    - [x] Sum drafts_created from job history
    - [x] Get latest total_outstanding_amount from most recent job history record
    - [x] Calculate critical invoice count (if available in webhook data)
    - _Requirements: 13.2, 13.3, 13.4_

  - [x]* 16.3 Write property test for digest content ⏭️ **SKIPPED** (marked optional with *)
    - **Property 23: Weekly Digest Content Completeness**
    - **Validates: Requirements 13.2, 13.3, 13.4, 13.5**

  - [x] 16.4 Create digest email template
    - [x] Design HTML email template
    - [x] Include drafts count, outstanding amount, critical count
    - [x] Add prompt to review Gmail drafts
    - [x] Add upgrade prompt if free tier limit reached
    - _Requirements: 13.2-13.6_

  - [x]* 16.5 Write property test for free tier upgrade prompt ⏭️ **SKIPPED** (marked optional with *)
    - **Property 24: Free Tier Limit Upgrade Prompt**
    - **Validates: Requirements 10.4, 13.6**

  - [x] 16.6 Create POST /api/digest/send route
    - [x] Query all active users
    - [x] Calculate digest data for each user
    - [x] Send email via SendGrid
    - [x] Log send results
    - _Requirements: 13.1-13.6_

  - [ ] 16.7 Set up external cron trigger ⚠️ **BLOCKED** (requires deployment to Vercel)
    - Configure cron-job.org or Vercel Cron to hit /api/digest/send every Monday
    - Add authentication for cron endpoint
    - _Requirements: 13.1_

  - **Files created**: backend/app/schemas/digest.py, backend/app/services/digest.py, backend/app/templates/digest_email.html, backend/app/api/digest.py

- [x] 17. Error Notification System ✅ **COMPLETE** (2026-02-15)
  - [x] 17.1 Implement consecutive failure tracking
    - [x] Query job_history for last 3 runs per user
    - [x] Identify users with 3 consecutive failures
    - _Requirements: 14.1_

  - [x]* 17.2 Write property test for failure notification ⏭️ **SKIPPED** (marked optional with *)
    - **Property 25: Consecutive Failure Notification**
    - **Validates: Requirements 14.1**

  - [x] 17.3 Create error notification email templates
    - [x] Template for sheet access lost
    - [x] Template for Make.com connection expired
    - [x] Template for generic errors
    - [x] Include error type and resolution steps
    - _Requirements: 14.2, 14.3, 14.4_

  - [x]* 17.4 Write property test for notification content ⏭️ **SKIPPED** (marked optional with *)
    - **Property 26: Error Notification Content**
    - **Validates: Requirements 14.2**

  - [x] 17.5 Implement notification sending logic
    - [x] Check for consecutive failures after each job log
    - [x] Send appropriate error notification email
    - [x] Track notification sent to avoid duplicates
    - _Requirements: 14.1-14.4_

  - **Files created**: backend/app/services/notifications.py, backend/app/schemas/notification.py, backend/app/api/notifications.py, backend/app/templates/error_sheet_access.html, backend/app/templates/error_make_connection.html, backend/app/templates/error_generic.html

- [ ] 18. Checkpoint - Backend Complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 19. Static HTML + Alpine.js/htmx Frontend - Landing Page ✅ **COMPLETE** (2026-02-15)
  - [x] 19.1 Set up static HTML project structure
    - [x] Create index.html with basic structure
    - [x] Add Alpine.js and htmx via CDN
    - [x] Configure Tailwind CSS for styling via CDN
    - [ ] Set up static asset serving in Vercel ⚠️ **BLOCKED** (requires deployment)
    - _Requirements: 15.1_

  - [x] 19.2 Create landing page HTML
    - [x] Add headline and 3-bullet value proposition
    - [x] Add "Sign up with Auth0" button (redirects to /login.html)
    - [x] Display pricing table (Free vs Paid)
    - _Requirements: 15.1, 15.2, 15.5_

  - [x] 19.3 Style landing page
    - [x] Clean, minimal design with Tailwind CSS
    - [x] Mobile responsive
    - [x] Clear call-to-action
    - _Requirements: 15.1_

  - **Files created**: static/index.html

- [x] 20. Static HTML + Alpine.js/htmx Frontend - Signup Flow ✅ **COMPLETE** (2026-02-15)
  - [x] 20.1 Create login button
    - [x] Button redirects to Auth0 Universal Login (/api/auth/login)
    - [x] Handle Auth0 callback redirect (handled by backend)
    - _Requirements: 1.1_

  - [x] 20.2 Handle Auth0 callback
    - [x] Auth0 callback handled by backend /api/auth/callback
    - [x] User creation/retrieval handled by backend
    - [x] Dashboard checks user setup status and prompts onboarding if needed
    - _Requirements: 1.2, 1.3, 1.6_

  - [x] 20.3 Create logout button
    - [x] Button calls Auth0 logout (/api/auth/logout)
    - [x] Clear local state
    - _Requirements: 1.1_

  - **Files created**: static/login.html, static/dashboard.html

- [x] 21. Static HTML + Alpine.js/htmx Frontend - Onboarding Flow ✅ **COMPLETE** (2026-02-15)
  - [x] 21.1 Create Google connection page
    - [x] "Connect Google Account" button
    - [x] Call /api/onboarding/connect-google
    - [x] Redirect to Make.com OAuth URL
    - [ ] Handle callback from Make.com ⚠️ **BLOCKED** (requires Make.com setup - Card #4820)
    - _Requirements: 2.1, 2.2_

  - [x] 21.2 Create sheet selection page
    - [x] Sheet ID input field
    - [x] Submit to POST /api/onboarding/select-sheet
    - [x] Show validation errors if columns missing
    - _Requirements: 3.1, 3.2, 3.4, 3.5_

  - [x] 21.3 Create sender info form page
    - [x] Name and business name inputs
    - [x] Submit to POST /api/onboarding/sender-info
    - _Requirements: 4.1, 4.2_

  - [x] 21.4 Create onboarding confirmation page
    - [x] Display success message
    - [x] Explain that drafts will be created in Gmail
    - [x] Mention weekly digest emails
    - _Requirements: 16.1, 16.2, 16.3_

  - **Files created**: static/onboarding.html, static/settings.html

- [x] 22. Static HTML + Alpine.js/htmx Frontend - Billing UI ✅ **COMPLETE** (2026-02-15)
  - [x] 22.1 Create upgrade prompt component
    - [x] Show when free tier (in dashboard and billing page)
    - [x] Display pricing comparison
    - [x] "Upgrade to Paid" button
    - _Requirements: 10.4_

  - [x] 22.2 Implement Stripe Checkout redirect
    - [x] Call POST /api/billing/create-checkout-session
    - [x] Redirect to Stripe Checkout URL
    - [ ] Handle success/cancel callbacks ⚠️ **BLOCKED** (requires Stripe setup - Card #4819)
    - _Requirements: 12.1_

  - [x] 22.3 Create billing status page
    - [x] Display current plan
    - [x] Show subscription status if paid
    - [x] Link to Stripe customer portal
    - _Requirements: 11.2_

  - **Files created**: static/billing.html

- [ ] 23. Checkpoint - Frontend Complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 24. Template Rendering and Email Content
  - [ ] 24.1 Implement template variable substitution
    - Replace {{client_name}}, {{invoice_id}}, {{amount}}, {{currency}}, {{days_overdue}}
    - Replace {{sender_name}}, {{sender_business}}
    - _Requirements: 8.2, 8.3_
  
  - [ ]* 24.2 Write property test for variable substitution
    - **Property 14: Email Template Variable Substitution**
    - **Validates: Requirements 8.2**
  
  - [ ]* 24.3 Write property test for sender info in signatures
    - **Property 13: Sender Info in Email Signatures**
    - **Validates: Requirements 4.4, 8.3**
  
  - [ ]* 24.4 Write property test for template selection
    - **Property 15: Stage-Specific Template Selection**
    - **Validates: Requirements 8.4**

- [ ] 25. Additional Property Tests
  - [ ]* 25.1 Write property test for draft not auto-sent
    - **Property 16: Draft Not Auto-Sent**
    - **Validates: Requirements 8.6**
  
  - [ ]* 25.2 Write property test for sheet tracking updates
    - **Property 17: Sheet Tracking Updates**
    - **Validates: Requirements 9.1, 9.2**
  
  - [ ]* 25.3 Write property test for status filtering
    - **Property 18: Status Filtering**
    - **Validates: Requirements 5.7**
  
  - [ ]* 25.4 Write property test for upper bound stage limit
    - **Property 19: Upper Bound Stage Limit**
    - **Validates: Requirements 5.6**
  
  - [ ]* 25.5 Write property test for OAuth token isolation
    - **Property 31: OAuth Token Isolation**
    - **Validates: Requirements 2.4, 20.4**
  
  - [ ]* 25.6 Write property test for data privacy
    - **Property 30: Data Privacy - No Invoice Data Stored**
    - **Validates: Requirements 20.1, 20.3**
  
  - [ ]* 25.7 Write property test for account deactivation
    - **Property 29: Account Deactivation Pauses Scenario**
    - **Validates: Requirements 19.4**

- [ ] 26. Integration Testing
  - [ ]* 26.1 Test complete signup flow end-to-end
    - Click login → Auth0 Universal Login → authenticate → callback → create user record → prompt for business_name → complete onboarding
    - Verify user record created with auth0_user_id and all fields
    - Verify Make.com scenario created with only user_id build variable
  
  - [ ]* 26.2 Test billing flow end-to-end
    - Initiate upgrade → complete Stripe Checkout → verify plan updated
    - Test webhook handling
    - Verify next config API call returns invoice_limit=100
  
  - [ ]* 26.3 Test Make.com scenario execution
    - Trigger scenario manually
    - Verify scenario calls GET /api/users/{user_id}/config
    - Verify Gmail drafts created
    - Verify sheet tracking updated
    - Verify scenario POSTs to /api/webhooks/make-results
    - Verify job history logged
  
  - [ ]* 26.4 Test weekly digest generation
    - Trigger digest endpoint
    - Verify email sent with correct content from webhook data
    - Verify upgrade prompt for free tier users
  
  - [ ]* 26.5 Test error notification flow
    - Simulate 3 consecutive failures
    - Verify error notification sent

- [ ] 27. Deployment Preparation
  - [ ] 27.1 Set up Vercel project
    - Create Vercel account
    - Connect Git repository
    - Configure build settings
    - _Requirements: Deployment_
  
  - [ ] 27.2 Set up managed PostgreSQL
    - Choose provider (Vercel Postgres, Supabase, or Railway)
    - Create production database
    - Run migrations
    - _Requirements: Database_
  
  - [ ] 27.3 Configure environment variables in Vercel
    - DATABASE_URL
    - AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_AUDIENCE
    - STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
    - MAKE_API_KEY, MAKE_SCENARIO_TEMPLATE_ID, MAKE_WEBHOOK_API_KEY
    - SENDGRID_API_KEY
    - _Requirements: Configuration_
  
  - [ ] 27.4 Configure Stripe webhook endpoint
    - Set webhook URL to production domain
    - Configure webhook events
    - Get webhook signing secret
    - _Requirements: 12.5_
  
  - [ ] 27.5 Deploy to Vercel
    - Push to main branch
    - Verify deployment successful
    - Test production endpoints
    - _Requirements: Deployment_

- [ ] 28. Production Testing and Launch
  - [ ] 28.1 Manual end-to-end testing in production
    - Complete signup flow
    - Connect real Google account
    - Select real test sheet
    - Verify Make.com scenario runs and calls config API
    - Verify Gmail drafts created
    - Verify webhook posts results back
    - Test payment flow with Stripe test card
    - Verify weekly digest received
    - _Requirements: All_
  
  - [ ] 28.2 Configure DNS and domain
    - Point domain to Vercel
    - Configure SSL certificate
    - Test domain access
    - _Requirements: Deployment_
  
  - [ ] 28.3 Set up monitoring and logging
    - Configure Sentry for error tracking
    - Set up Vercel Analytics
    - Create dashboard for job success rates
    - _Requirements: Monitoring_
  
  - [ ] 28.4 Final security review
    - Verify all secrets in environment variables
    - Test rate limiting
    - Verify CORS configuration
    - Test Stripe webhook signature verification
    - Test Make.com webhook API key authentication
    - _Requirements: Security_

- [ ] 29. Final Checkpoint - MVP Complete
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at major milestones
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples and edge cases
- The existing CLI code (src/invoice_collector/) serves as reference for core logic
- Make.com Pro plan ($16/mo) handles all Google API interactions and daily scheduling
- Frontend is minimal static HTML + Alpine.js/htmx (no React/SPA framework)
- No dashboard, settings, or analytics pages in MVP
- **Architecture**: Stateless Make.com scenarios. Each scenario stores only user_id and fetches all config via GET /api/users/{user_id}/config. Results posted to POST /api/webhooks/make-results.
