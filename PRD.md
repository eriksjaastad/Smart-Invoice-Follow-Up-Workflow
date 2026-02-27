# PRD: Smart Invoice Workflow — Hosted SaaS MVP

**Version:** 1.1
**Author:** Erik Sjaastad + Claude (Super Manager)
**Date:** 2026-02-15
**Status:** Approved (2026-02-09) · Updated 2026-02-15 (operational guardrails, go/no-go gates)

---

## Overview

Smart Invoice Workflow is a hosted SaaS that automates invoice follow-up for small businesses. Users sign up, connect their Google account through Make.com's verified integration, pick their invoice spreadsheet, and the system creates Gmail drafts with escalating payment reminders on a 42-day schedule. Weekly digest emails prove the system is working. No setup, no configuration, no terminal.

**One sentence:** "Stop chasing invoices. We do it for you."

**Product form:** Hosted SaaS. Customer signs up on our website, connects Google through Make.com's verified integration, and the system runs automatically. Make.com handles the Google API work; we handle the user experience.

**Company:** Synth Insight Labs (domain, email, social accounts ready)

---

## Goals

1. **Get one paying customer.** Revenue target: $5. The real goal is learning to sell.
2. **Prove the product works as a service.** Take the existing working Python CLI (7 source files, 41 tests) and wrap it in a web app that non-technical users can operate.
3. **Ship in 2.5 weeks from PRD sign-off.** Hard deadline. No scope creep.
4. **Zero-friction onboarding.** Sign up with Google, pick a sheet, done. Under 2 minutes.
5. **Learn distribution.** Post on Product Hunt, Reddit, Indie Hackers, LinkedIn. Spend exactly 2 days on distribution, then stop and measure.

---

## Non-Goals

These are explicitly OUT of MVP. Do not build them. Do not plan for them. Do not design the database to accommodate them.

- Custom email templates
- Custom escalation schedules
- Multi-user / team accounts
- Dashboard / analytics / reporting
- Stripe payment collection (we remind, we don't collect money)
- Invoice creation or PDF generation
- API for third-party integrations
- Mobile app
- Slack/Teams notifications
- AI-powered email personalization
- White-label / reseller program
- CRM features
- Accounting features
- Custom column mapping for Google Sheets (v2 feature)
- Market research (build first, research later)

---

## Target Users

**Primary:** Non-technical small business owners who:
- Send invoices (consultants, freelancers, agencies, contractors, service businesses)
- Use Google Workspace (Gmail + Google Sheets) — or could easily
- Hate chasing payments but can't afford a bookkeeper
- Will never open a terminal, install Python, or configure API keys
- Would pay $10-20/month to make this problem go away

**Not our customer:**
- Enterprise with accounts receivable departments
- Businesses using Xero/QuickBooks integrated collections
- Anyone who needs custom invoicing (we don't create invoices)
- Technical users who'd just run the open-source CLI

---

## Problem Statement

Small business owners, freelancers, and consultants lose thousands of dollars and dozens of hours every month chasing overdue invoices.

- Send invoice, forget about it, realize 45 days later it's unpaid, send awkward email, repeat
- Average collection time without follow-up: 45+ days
- 15-20% of invoices never get paid at all
- 6-8 hours/week spent on manual follow-up

Solutions exist (accounting software, collection agencies) but they're too complex, too expensive, or too aggressive for small businesses. The existing open-source Smart Invoice CLI solves the problem technically, but requires Python, Google Cloud credentials, and a terminal — making it useless for the target customer.

---

## Core Concept / Data Model

### How It Works

1. User signs up on our site
2. User connects their Google account via Make.com (verified OAuth — no scary warnings)
3. User picks their Google Sheet with invoice data (or creates from our template)
4. User enters their name and business name (for email signatures)
5. Make.com scenario runs daily: reads the sheet, finds overdue invoices, determines escalation stage
6. System creates Gmail drafts with personalized reminders (sender's name + business in signature)
7. User reviews drafts in Gmail, hits Send (or edits first)
8. System updates the sheet to track which stage was sent
9. Weekly digest email summarizes what was done and highlights critical invoices

### The 6-Stage Escalation Sequence (42 days, fixed in MVP)

| Stage | Day | Tone |
|-------|-----|------|
| 1 | 7 | Friendly check-in ("just making sure you received this") |
| 2 | 14 | Direct follow-up ("checking on invoice status") |
| 3 | 21 | Urgent ("this is now 3 weeks overdue") |
| 4 | 28 | Firm ("let's schedule a call to discuss") |
| 5 | 35 | Final warning ("last reminder before escalation") |
| 6 | 42 | Last notice ("next steps if no payment received") |

### Data Model

**Users Table**

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| email | TEXT | From Google profile |
| name | TEXT | From Google profile |
| business_name | TEXT | User-provided during onboarding |
| sheet_id | TEXT | Their Google Sheet ID |
| make_scenario_id | TEXT | Their cloned Make.com scenario ID |
| active | BOOLEAN | Can pause service |
| plan | TEXT | "free" or "paid" |
| created_at | TIMESTAMP | |
| last_run_at | TIMESTAMP | Last successful daily check |

**Job History Table**

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| run_at | TIMESTAMP | |
| invoices_checked | INT | |
| drafts_created | INT | |
| errors | TEXT | JSON array of errors, if any |

**No invoice data stored on our side.** The Google Sheet is the source of truth. We read it, act on it, and log what we did. Privacy-friendly.

**Google Sheet Column Schema (LOCKED — v1)**

This is the canonical column layout for the Invoice Tracker sheet. All Make.com scenarios (Create Template, Daily Processing, Validate Sheet) depend on this exact order. Do NOT add, remove, or reorder columns without updating all scenarios.

| Column | Index | Header | Type | Required | Description |
|--------|-------|--------|------|----------|-------------|
| A | 0 | `Invoice_Number` | Text | Yes | Unique invoice identifier |
| B | 1 | `Client_Name` | Text | Yes | Client display name |
| C | 2 | `Client_Email` | Email | Yes | Email for draft reminders |
| D | 3 | `Amount` | Number | Yes | Invoice amount (no $ or commas) |
| E | 4 | `Due_Date` | Date | Yes | Payment due date (YYYY-MM-DD) |
| F | 5 | `Sent_Date` | Date | Yes | When invoice was originally sent |
| G | 6 | `Paid` | Boolean | Yes | `TRUE` or `FALSE` |
| H | 7 | `Last_Stage_Sent` | Number | Auto | Escalation tier (7/14/21/28/35/42) |
| I | 8 | `Last_Sent_At` | Date | Auto | Date last draft was created |

Custom column mapping is a v2 feature. For MVP, the sheet must match this exact layout.

---

## Functional Requirements

### Authentication
- FR-1: Users sign up via Auth0 (email/password or magic link — managed auth, no homebrew security)
- FR-2: Users connect their Google account through Make.com's verified OAuth integration (no "unverified app" warnings — Make.com is already verified by Google)
- FR-3: Make.com handles Google token storage and refresh — we never touch Google OAuth tokens directly

### Sheet Connection
- FR-4: After auth, user sees a list of their Google Sheets and picks one
- FR-5: Alternative: user can create a new sheet from our template
- FR-6: System validates the sheet has required columns matching our fixed template (client name, invoice amount, date sent, status/days overdue). Custom column mapping is a v2 feature.
- FR-7: If columns are missing, show a clear error with instructions and a link to the template

### Daily Processing
- FR-8: Make.com scenario runs once daily per user (scheduled scenario)
- FR-9: For each overdue invoice, determine the correct escalation stage based on days overdue
- FR-10: Create a Gmail draft with the appropriate template for that stage
- FR-11: Update the Google Sheet to record which stage was sent and when
- FR-12: Skip invoices already at stage 6 (42+ days) — no further automated action

### Email Drafts
- FR-13: Drafts use the user's own Gmail address as the sender
- FR-14: Drafts are NOT auto-sent — they appear in the user's Gmail Drafts folder
- FR-15: Email templates use the 6-stage escalation copy (fixed in MVP, no customization)
- FR-16: Templates include the client name, invoice amount, invoice number, and sender's name + business name in the signature

### Billing
- FR-17: Free tier: up to 3 overdue invoices processed per daily run (system skips additional overdue invoices beyond 3)
- FR-18: Paid tier: unlimited invoices, $15/month or $120/year
- FR-19: Payment via Stripe Checkout
- FR-20: When free tier limit reached, show upgrade prompt (don't silently stop working)

### Operational Guardrails (Added 2026-02-15 — not yet implemented)
- FR-21: **Global kill switch** — DB flag or env flag (`SYSTEM_PAUSED=true`). When enabled, `GET /api/users/{id}/config` returns `paused=true` and Make.com scenario exits early with zero drafts created. One-click to pause all processing.
- FR-22: **Per-run hard cap (paid tier)** — Even paid users are capped at 100 invoices per daily run. Prevents spreadsheet explosions (user pastes 10,000 rows). Enforced via `invoice_limit` in `/config` response.
- FR-23: **Fail closed on bad sheet format** — If column validation fails during a daily run, create zero drafts and zero sheet writes. Log the failure. Never partially process a malformed sheet.
- FR-24: **Serialize draft creation** — No parallel draft bursts per user. Create drafts sequentially to prevent Gmail rate issues and limit blast radius if logic is wrong.

### Weekly Digest
- FR-25: System sends a weekly summary email to each active user (every Monday)
- FR-26: Digest includes: number of drafts created that week, total outstanding amount, count of critical invoices (35+ days overdue), and a prompt to review Gmail drafts
- FR-27: Digest serves as proof-of-value — reminds user the system is working and justifies the subscription

---

## Non-Functional Requirements

- NFR-1: **Uptime:** 99%+ for daily job execution (users depend on this running reliably)
- NFR-2: **Latency:** Sheet processing completes in < 30 seconds per user
- NFR-3: **Security:** Make.com manages all OAuth tokens. No full Gmail access — only `gmail.compose`
- NFR-4: **Privacy:** No invoice data stored on our servers. Sheet is the source of truth.
- NFR-5: **Scalability:** Support at least 100 users before needing infrastructure changes (plenty for MVP)
- NFR-6: **Monitoring:** Log every job run with success/failure counts. Alert on 3+ consecutive failures for any user.
- NFR-7: **Monitoring (expanded, added 2026-02-15 — not yet implemented):** Alert on 0 runs recorded in 48 hours (system-level dead-man switch). Alert on draft spike anomaly (e.g., >20 drafts/day/user). Alert if weekly digest job fails. Log digest sends.
- NFR-8: **Cost:** Make.com Pro ($16/mo) + Vercel (free tier). Target under $30/month at launch.

---

## UX and UI Requirements

### Landing Page
- UX-1: Single page with: headline, 3-bullet value prop, "Sign up with Google" button, pricing
- UX-2: No navigation menu. No blog. No "About us." One page, one action.
- UX-3: Social proof: the $47K collection case study results (with permission)

### Signup Flow
- UX-4: Sign up → connect Google via Make.com (verified, no warnings) → pick sheet → enter your name + business name → done
- UX-5: Total setup time: under 2 minutes
- UX-6: No settings page in MVP. No profile page. No dashboard.
- UX-7: After setup, show a confirmation: "You're all set. We'll create drafts in your Gmail when invoices are overdue. You'll get a weekly summary every Monday."

### Ongoing Experience
- UX-8: The product is invisible after setup. It just works in the background.
- UX-9: User's primary touchpoint is Gmail — they see drafts, review them, send them.
- UX-10: Weekly digest email every Monday — summarizes drafts created, outstanding amounts, critical invoices. Proves value and drives engagement.
- UX-11: If something goes wrong (sheet access lost, Make.com connection expired), send an email notification to the user.

---

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|-------------|
| First paying customer | 1 | Stripe dashboard |
| Revenue | $5 | Stripe dashboard |
| Time to sign up | < 2 minutes | Manual testing |
| Daily job reliability | 99%+ | Job history logs |
| Support tickets | < 5/week | Email inbox |
| Signups (free + paid) | 10 in first month | Users table |

**The real metric: Did we learn how to sell?** Revenue is secondary to the learning.

---

## MVP Scope

### In Scope
- User signup (email/password or magic link)
- Google account connection via Make.com (verified OAuth, no warnings)
- Google Sheet connection (pick or create from template)
- Daily automated processing via Make.com scenarios
- Gmail draft creation with 6-stage escalation templates (with sender name + business in signature)
- Sheet tracking updates (which stage was sent)
- Weekly digest email (proof-of-value summary every Monday)
- Free tier (3 invoices) + paid tier ($15/month via Stripe)
- Landing page with signup
- Error notification emails

### Out of Scope
- Everything listed in Non-Goals above
- Admin panel
- User settings/preferences
- Multiple sheets per user
- Anything that doesn't directly serve: sign up → connect sheet → get drafts

### What We Reuse From Existing Code
- `src/invoice_collector/router.py` — escalation logic (which stage based on days overdue) — ported into Make.com scenario logic
- Email templates — the 6-stage escalation copy (updated with sender name + business signature)
- `tests/` — existing test suite as reference for edge cases

### What We Rebuild
- **Make.com scenario** — new build: reads Google Sheet, determines escalation stage, creates Gmail drafts, updates sheet tracking
- **Web app** — new build: landing page, user signup, onboarding flow (connect Google via Make.com), billing, weekly digest
- `config.py` / `main.py` / `sheets.py` — replaced by Make.com (no longer needed as direct code)
- New: user management, Make.com scenario management, Stripe integration, digest email service

---

## Constraints / Technical Stack

### Stack
- **Backend:** Python + FastAPI (user management, billing, digest emails)
- **Automation layer:** Make.com (handles Google OAuth, Sheets API, Gmail API, daily scheduling)
- **Auth (our app):** Auth0 — email/password or magic link (free up to 7,500 MAU, no homebrew auth)
- **Auth (Google):** Make.com's verified OAuth — users connect Google through Make.com, no verification needed
- **Database:** PostgreSQL (user accounts, Make.com scenario IDs, job history)
- **Job scheduler:** Make.com scenarios (scheduled daily per user — replaces APScheduler/Celery)
- **Payments:** Stripe Checkout
- **Frontend:** Static HTML + Alpine.js or htmx (no SPA framework — landing page + 4-step onboarding doesn't justify React)
- **Hosting:** Vercel (serverless — no background job support needed, Make.com handles scheduling)
- **Domain:** synthinsightlabs.com (subdomain or subpath TBD)

### Google OAuth (via Make.com)
Make.com requests the Google scopes on our behalf. Users authorize through Make.com's consent screen (already verified by Google). We never handle Google OAuth tokens directly.

Scopes requested by Make.com:
- `gmail.compose` — create draft emails
- `spreadsheets` — read/write invoice data

### Governance
- All code in `src/`
- Tests required for core logic (reuse + extend existing 41 tests)
- No hardcoded credentials — all secrets via environment variables
- Commits linked to task IDs
- `trash` not `rm` for file operations

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Make.com dependency — pricing changes or API limits | Medium | Cost increase or service disruption | Make.com Pro plan: 10,000 ops/month (~20 active users at ~480 ops/user/mo). Monitor usage. Existing Python code is a fallback migration path to direct Google API if needed. |
| Make.com API doesn't support programmatic per-user scenario creation | ~~Medium~~ Resolved | ~~Architecture change~~ N/A | **Confirmed:** Make.com API supports `POST /scenarios`, `POST /scenarios/{id}/clone`, and `POST /connections`. Pro plan ($16/mo) required. |
| Users don't have sheets in the right format | Medium | Bad onboarding | Provide a template sheet. Validate columns on setup with clear error messages. |
| Gmail draft creation rate limits | Low | Service degradation | Google allows 250 drafts/day per user. Far exceeds needs. |
| Nobody pays | High | No revenue | Expected outcome. Free tier keeps it alive. The goal is learning, not profit. |
| Scope creep during build | High | Missed deadline | This PRD is the firewall. Non-Goals section is the law. |
| Hosting + Make.com costs exceed revenue | Medium | Net loss | Make.com Pro ($16/mo) + Vercel free tier. ~$20/month floor. Kill switch if costs spike. |

---

## Timeline

### Original Estimate (Feb 2026)

| Phase | Duration | What |
|-------|----------|------|
| **Design** | 2 days | Database schema, API routes, Make.com scenario design, deploy target |
| **Core rebuild** | 5 days | Make.com scenario build, web app (signup, onboarding, billing, digest) |
| **Frontend** | 2 days | Landing page, signup flow, sheet picker |
| **Payment** | 1 day | Stripe Checkout integration |
| **Testing** | 2 days | End-to-end: signup, sheet, drafts, payment |
| **Ship** | 1 day | Deploy, DNS, monitoring |
| **Distribution** | 2 days | Product Hunt, Reddit, LinkedIn posts |
| **Total** | ~2.5 weeks | |

**Original start:** Week of Feb 17. **Original ship target:** ~March 1.

### Revised Timeline (Updated 2026-02-27)

Design, core build, frontend, and payment phases are complete. Accounts (Auth0, Stripe, Resend, Make.com) are set up. Make.com has 2 of 4 scenarios working. What remains is bug fixes, deploy, and testing.

| Phase | Target Date | What | Status |
|-------|-------------|------|--------|
| **Bug fixes** | Feb 28 - Mar 2 | auth.py fix (#4953), kill switch (#4823), Make.com POST URL (#4945) | In Progress |
| **Deploy** | Mar 3 - 4 | Vercel deploy (#4779), DNS, env vars, update Make.com POST URL | Not Started |
| **E2E Testing** | Mar 5 - 6 | Full signup → sheet → drafts → payment flow (#4778) | Not Started |
| **Ship** | Mar 7 | Smoke test, monitoring live, kill switch verified | Target |
| **Distribution** | Mar 8 - 9 | Product Hunt, Reddit, LinkedIn (#4780) | Not Started |

**Revised ship target:** March 7, 2026 (1 week slip from original).

**Operational tracking:** See `SHIP_CHECKLIST.md` for current state, env vars, deploy sequence, and step-by-step ship instructions.

### Go/No-Go Gates (Added 2026-02-15)

Each gate is a hard checkpoint. Do not proceed past a gate until all items pass.

**Gate A — End of Design (after Day 2)**
- [ ] DB schema finalized (Users + Job History + global kill switch flag)
- [ ] Make.com scenario blueprint approved (modules + config GET + results POST)
- [ ] API route contracts defined (`/config`, `/make-results`, auth endpoints)

**Gate B — End of Core Build (after Day 7)**
- [ ] 1 test user can: signup → connect Google → pick sheet → daily scenario creates drafts → results posted back
- [ ] Global kill switch works (pauses all processing)
- [ ] Per-user `active=false` blocks processing
- [ ] Free tier cap enforced (3 invoices)

**Gate C — End of Testing (after Day 11)**
- [ ] E2E on free + paid tiers
- [ ] Kill switch drill passed (global + per-user)
- [ ] Failure alerts verified (3 consecutive failures triggers alert)
- [ ] Draft cap verified (paid tier capped at 100/run)
- [ ] Fail-closed verified (bad sheet format → zero drafts)

**Gate D — Ship Day (Day 12)**
- [ ] DNS, SSL, production env vars confirmed
- [ ] Monitoring live (logs streaming, alert channels working)
- [ ] Kill switch is one-click available
- [ ] Weekly digest scheduler ready (Monday)
- [ ] Smoke test: fresh user, end-to-end, drafts in Gmail

---

## Resolved Questions (2026-02-14)

1. **Hosting provider:** Vercel. Serverless is fine — Make.com handles all long-running work.
2. **Make.com API:** Confirmed — supports programmatic scenario creation, cloning, and connection management. Pro plan required ($16/mo).
3. **Make.com pricing:** Pro plan = 10,000 ops/month. ~480 ops/user/month at 5 invoices. Supports ~20 active users. Detailed pricing model deferred to pre-launch (Task #4810).
4. **Sheet format:** Fixed template for MVP. Custom column mapping is a v2 feature.
5. **Product name:** "Smart Invoice" for now. Name research before public launch (Task #4811).
6. **Legal:** ToS and Privacy Policy needed before launch. Erik has no prior software legal experience — research needed (Task #4812).
7. **Sender info:** User enters name + business name during onboarding (stored in Users table). Used in email signatures per FR-16.

---

## Make.com ↔ Backend Data Flow (Resolved 2026-02-14)

Research tasks #4814, #4815, #4816 — all resolved by a single architecture decision.

### Architecture: Stateless Scenarios, Backend as Brain

Each user's Make.com scenario stores only one thing: the user's ID (set once via build variable after cloning). The scenario is stateless — our backend is the single source of truth for all user config and plan data.

### Runtime Flow (every scheduled daily run)

1. **First module — HTTP GET to our API:**
   `GET /api/users/{user_id}/config` returns `sheet_id`, `sender_name`, `business_name`, `plan`, `invoice_limit`. This answers Q1 (user config) and Q3 (free tier enforcement) in one call.

2. **Processing modules** use the API response: `sheet_id` for which sheet to read, `sender_name`/`business_name` for email signatures, `invoice_limit` to cap the Google Sheets row limit (`3` for free, `100` for paid).

3. **Last module — HTTP POST back to our API:**
   `POST /api/webhooks/make-results` with `user_id`, `drafts_created`, `total_outstanding_amount`. Uses a Numeric Aggregator module to sum amounts and count drafts before posting. This answers Q2 (digest data).

### Why This Works

- **One source of truth:** User updates business name or upgrades plan → next run picks it up automatically.
- **No stale config:** Nothing to keep in sync between our DB and Make.com scenario variables.
- **Scheduled runs just work:** No API trigger needed — scenario runs on Make.com's daily schedule and fetches what it needs.
- **Simple cloning:** `POST /scenarios/{id}/clone` → set one build variable (`user_id`) → activate schedule → done.

### Required Backend Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/users/{user_id}/config` | GET | Scenario fetches all user config + plan tier at start of each run |
| `/api/webhooks/make-results` | POST | Scenario reports run results for digest emails |

---

## Distribution Plan (Post-Ship)

Free channels only. No ads for v1.

1. **Product Hunt** — launch post
2. **Reddit** — r/smallbusiness, r/freelance, r/entrepreneur, r/SaaS
3. **Indie Hackers** — build-in-public post
4. **LinkedIn** — company page + personal post
5. **Twitter/X** — company account
6. **Facebook Groups** — business groups (Erik has business account)

**Hard cap: 2 days on distribution.** Post, then stop and see what sticks.

---

## Existing Assets

- **Company:** Synth Insight Labs — domain, email, social accounts ready
- **Code:** Working Python implementation (7 source files, 41 tests, proven escalation logic) — serves as reference for Make.com scenario build
- **Make.com experience:** Blueprint exists from instructor (lead autoresponder, not invoice-specific). Demonstrates the platform's email + Google integration capabilities.
- **Facebook business account:** Ready
- **Case study data:** $47K collection results from instructor's consulting firm

---

*This PRD is the input for Kiro specs generation (Task #4746). Do not front-run Kiro — no user stories, no EARS requirements, no detailed database schemas beyond what's outlined here.*
