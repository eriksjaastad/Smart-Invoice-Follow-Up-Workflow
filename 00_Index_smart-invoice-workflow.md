---
tags:
  - map/project
  - p/smart-invoice-workflow
  - type/saas
  - domain/business-automation
  - status/active
created: 2026-01-02
updated: 2026-02-15
---

# smart-invoice-workflow: Index

Hosted SaaS that automates invoice follow-up for small businesses. Users sign up, connect Google via Make.com, pick their invoice sheet, and the system creates escalating Gmail draft reminders on a 42-day schedule.

**Company:** Synth Insight Labs
**Revenue model:** Free (3 invoices/day) + Paid ($15/month, 100 invoices/day)

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy (async PostgreSQL)
- **Frontend:** Static HTML + Alpine.js (Vercel)
- **Auth:** Auth0
- **Automation:** Make.com Pro
- **Payments:** Stripe Checkout
- **Email:** SendGrid

## External Services

- Auth0 (authentication)
- Make.com (Google Sheets/Gmail automation)
- Stripe (billing)
- SendGrid (digest + notification emails)
- Vercel (hosting)
- PostgreSQL (database)

## Key Endpoints

- `GET /api/users/{id}/config` — Make.com calls this to get user config
- `POST /api/webhooks/make-results` — Make.com reports daily run results
- `POST /api/webhooks/stripe` — Stripe payment webhooks
- `POST /api/digest/trigger` — Cron-triggered weekly digest

## Status

**Phase:** Active development (backend built, frontend in progress)
**Goal:** Ship MVP, get one paying customer
**PRD:** Approved 2026-02-09, updated 2026-02-15

scaffolding_version: 1.0.0
scaffolding_date: 2026-01-27

## Related Documentation

- [PRD](PRD.md) — Product requirements (source of truth)
- [PROPOSAL_FINAL](PROPOSAL_FINAL.md) — Traceability: PRD → Kiro specs
- [IMPLEMENTATION_PROGRESS](IMPLEMENTATION_PROGRESS.md) — Build tracker
- [LAUNCH_CHECKLIST](LAUNCH_CHECKLIST.md) — Pre-launch gates
- [RUNBOOK](RUNBOOK.md) — Operations manual
- [README](README.md) — Project overview and directory map

<!-- LIBRARIAN-INDEX-START -->

### Subdirectories

| Directory | Files | Description |
| :--- | :---: | :--- |
| [backend/](backend/) | 1 | No description available. |
| [case-studies/](case-studies/) | 4 | No description available. |
| [docs/](docs/) | 6 | No description available. |
| [make-blueprints/](make-blueprints/) | 5 | No description available. |
| [static/](static/) | 6 | No description available. |
| [test-results/](test-results/) | 0 | No description available. |

### Files

| File | Description |
| :--- | :--- |
| [AGENTS.md](AGENTS.md) | > The single source of truth for hierarchy, workflow, and AI collaboration philosophy. |
| [CLAUDE.md](CLAUDE.md) | **Python execution:** Never use `python` or `python3`. Always use `$HOME/.local/bin/uv run`. |
| [DECISIONS.md](DECISIONS.md) | > *Documenting WHY we made decisions, not just WHAT we built.* |
| [Integration HTTP, Google Sheets, Tools, Gmail.blueprint.json](Integration HTTP, Google Sheets, Tools, Gmail.blueprint.json) | No description available. |
| [MAKE_BUILDING_NOTES.md](MAKE_BUILDING_NOTES.md) | Lessons learned from building and importing SIW scenarios. Reference this before creating or debuggi... |
| [PRD.md](PRD.md) | **Version:** 1.1 |
| [PRIVACY_POLICY.md](PRIVACY_POLICY.md) | **Product:** Smart Invoice Workflow |
| [PROPOSAL_FINAL.md](PROPOSAL_FINAL.md) | **Document Version:** 1.0 |
| [README.md](README.md) | Hosted SaaS that automates invoice follow-up for small businesses. |
| [REVIEWS_AND_GOVERNANCE_PROTOCOL.md](REVIEWS_AND_GOVERNANCE_PROTOCOL.md) | This file is managed by sync_governance.py and will be OVERWRITTEN on the next sync. |
| [RUNBOOK.md](RUNBOOK.md) | This runbook is for **operating SIW safely** during MVP: diagnosing failures, preventing runaway beh... |
| [SHIP_CHECKLIST.md](SHIP_CHECKLIST.md) | **Last Updated:** 2026-02-27 |
| [START_HERE_TOMORROW.md](START_HERE_TOMORROW.md) | **Date:** 2026-03-12 |
| [TERMS_OF_SERVICE.md](TERMS_OF_SERVICE.md) | **Product:** Smart Invoice Workflow |
| [backend/alembic/env.py](backend/alembic/env.py) | Alembic environment configuration for async SQLAlchemy |
| [backend/alembic/script.py.mako](backend/alembic/script.py.mako) | No description available. |
| [backend/alembic/versions/001_initial_schema.py](backend/alembic/versions/001_initial_schema.py) | Initial schema: users and job_history tables |
| [backend/alembic/versions/002_add_system_state.py](backend/alembic/versions/002_add_system_state.py) | Add system_state table for global kill switch |
| [backend/alembic.ini](backend/alembic.ini) | No description available. |
| [backend/app/__init__.py](backend/app/__init__.py) | Smart Invoice SaaS Backend Application |
| [backend/app/api/__init__.py](backend/app/api/__init__.py) | API routes package. |
| [backend/app/api/auth.py](backend/app/api/auth.py) | Authentication API routes for Auth0 integration. |
| [backend/app/api/billing.py](backend/app/api/billing.py) | Billing API routes for Stripe integration. |
| [backend/app/api/cron.py](backend/app/api/cron.py) | Cron-triggered API routes. |
| [backend/app/api/digest.py](backend/app/api/digest.py) | Digest API routes for weekly email summaries. |
| [backend/app/api/notifications.py](backend/app/api/notifications.py) | Notification API routes for error notifications. |
| [backend/app/api/onboarding.py](backend/app/api/onboarding.py) | Onboarding flow API routes. |
| [backend/app/api/system.py](backend/app/api/system.py) | System control API routes. |
| [backend/app/api/users.py](backend/app/api/users.py) | User management API routes. |
| [backend/app/api/webhooks.py](backend/app/api/webhooks.py) | Webhook API routes for external integrations. |
| [backend/app/core/__init__.py](backend/app/core/__init__.py) | Core configuration and utilities |
| [backend/app/core/auth.py](backend/app/core/auth.py) | Auth0 authentication utilities. |
| [backend/app/core/config.py](backend/app/core/config.py) | Application configuration using Pydantic Settings |
| [backend/app/db/__init__.py](backend/app/db/__init__.py) | Database configuration and session management |
| [backend/app/db/session.py](backend/app/db/session.py) | Database session and engine configuration |
| [backend/app/main.py](backend/app/main.py) | FastAPI application entry point |
| [backend/app/models/__init__.py](backend/app/models/__init__.py) | Database models package. |
| [backend/app/models/job_history.py](backend/app/models/job_history.py) | Job history database model. |
| [backend/app/models/system_state.py](backend/app/models/system_state.py) | System state model for global operational flags. |
| [backend/app/models/user.py](backend/app/models/user.py) | User database model. |
| [backend/app/schemas/__init__.py](backend/app/schemas/__init__.py) | Pydantic schemas package. |
| [backend/app/schemas/digest.py](backend/app/schemas/digest.py) | Digest Pydantic schemas for weekly email digest functionality. |
| [backend/app/schemas/invoice.py](backend/app/schemas/invoice.py) | Invoice Pydantic schemas for validation. |
| [backend/app/schemas/job_history.py](backend/app/schemas/job_history.py) | Job history Pydantic schemas for request/response validation. |
| [backend/app/schemas/notification.py](backend/app/schemas/notification.py) | Notification Pydantic schemas for error notifications. |
| [backend/app/schemas/system.py](backend/app/schemas/system.py) | System state schemas for request/response validation. |
| [backend/app/schemas/user.py](backend/app/schemas/user.py) | User Pydantic schemas for request/response validation. |
| [backend/app/schemas/webhook.py](backend/app/schemas/webhook.py) | Webhook Pydantic schemas for Make.com integration. |
| [backend/app/services/__init__.py](backend/app/services/__init__.py) | Business logic services package. |
| [backend/app/services/digest.py](backend/app/services/digest.py) | Weekly digest email service. |
| [backend/app/services/escalation.py](backend/app/services/escalation.py) | Escalation logic for invoice reminders. |
| [backend/app/services/notifications.py](backend/app/services/notifications.py) | Error notification service. |
| [backend/app/services/system_state.py](backend/app/services/system_state.py) | Service helpers for global system state. |
| [case-studies/JP-Middleton.md](case-studies/JP-Middleton.md) | JP Middleton’s business, **StartGrowSell.ai** (and its operational arm **GymMembersNow**), is a stro... |
| [case-studies/business-sources.md](case-studies/business-sources.md) | To get past the "influencer" noise and find out where real business-to-business (B2B) deals actually... |
| [case-studies/gemini-ideas-business-research.md](case-studies/gemini-ideas-business-research.md) | import pandas as pd |
| [case-studies/pricing-research.md](case-studies/pricing-research.md) | Since you’re looking at an automated invoice service, your pricing model is actually your biggest co... |
| [docs/E2E_TESTING_PLAN.md](docs/E2E_TESTING_PLAN.md) | - Visual snapshot infrastructure complete (playwright.config.js, test files) |
| [docs/SUMMARY.md](docs/SUMMARY.md) | **Date:** 2026-03-11 |
| [docs/TOMORROW_MORNING_START_HERE.md](docs/TOMORROW_MORNING_START_HERE.md) | **Goal:** Get agent-driven E2E testing working in ~45 minutes |
| [docs/task_5104_prompt.md](docs/task_5104_prompt.md) | We have Vercel environments: Production, Preview, and Development. Currently DEBUG_MOCK_AUTH is only... |
| [docs/task_5105_prompt.md](docs/task_5105_prompt.md) | Playwright tests currently hardcode the production URL. We need to support testing against Preview d... |
| [docs/task_5106_prompt.md](docs/task_5106_prompt.md) | Tasks 5104 and 5105 set up Preview environment with mock auth and configured Playwright for multi-en... |
| [email_autoresponder.json](email_autoresponder.json) | No description available. |
| [main.py](main.py) | No description available. |
| [make-blueprints/SIW - Create Template.blueprint.json](make-blueprints/SIW - Create Template.blueprint.json) | No description available. |
| [make-blueprints/SIW - Daily Processing.blueprint (1).json](make-blueprints/SIW - Daily Processing.blueprint (1).json) | No description available. |
| [make-blueprints/SIW - List Sheets.blueprint.json](make-blueprints/SIW - List Sheets.blueprint.json) | No description available. |
| [make-blueprints/SIW - Validate Sheet.blueprint.json](make-blueprints/SIW - Validate Sheet.blueprint.json) | No description available. |
| [make-blueprints/SIW_Create_Template_blueprint.json](make-blueprints/SIW_Create_Template_blueprint.json) | No description available. |
| [package-lock.json](package-lock.json) | No description available. |
| [package.json](package.json) | No description available. |
| [playwright.config.js](playwright.config.js) | No description available. |
| [pyproject.toml](pyproject.toml) | No description available. |
| [skills-lock.json](skills-lock.json) | No description available. |
| [static/billing.html](static/billing.html) | No description available. |
| [static/dashboard.html](static/dashboard.html) | No description available. |
| [static/index.html](static/index.html) | No description available. |
| [static/login.html](static/login.html) | No description available. |
| [static/onboarding.html](static/onboarding.html) | No description available. |
| [static/settings.html](static/settings.html) | No description available. |
| [test-results/test_user_flows-Scenario-A-fecd8-ds-and-displays-key-content/error-context.md](test-results/test_user_flows-Scenario-A-fecd8-ds-and-displays-key-content/error-context.md) | - main [ref=e3]: |
| [test-results/test_user_flows-Scenario-A-fecd8-ds-and-displays-key-content-retry1/error-context.md](test-results/test_user_flows-Scenario-A-fecd8-ds-and-displays-key-content-retry1/error-context.md) | - main [ref=e3]: |
| [test-results/test_user_flows-Scenario-B-5caa5-dashboard-→-onboarding-flow/error-context.md](test-results/test_user_flows-Scenario-B-5caa5-dashboard-→-onboarding-flow/error-context.md) | - main [ref=e3]: |
| [test-results/test_user_flows-Scenario-B-5caa5-dashboard-→-onboarding-flow-retry1/error-context.md](test-results/test_user_flows-Scenario-B-5caa5-dashboard-→-onboarding-flow-retry1/error-context.md) | - main [ref=e3]: |
| [test-results/test_user_flows-Scenario-B-c96ca--page-loads-and-shows-steps/error-context.md](test-results/test_user_flows-Scenario-B-c96ca--page-loads-and-shows-steps/error-context.md) | - main [ref=e3]: |
| [test-results/test_user_flows-Scenario-B-c96ca--page-loads-and-shows-steps-retry1/error-context.md](test-results/test_user_flows-Scenario-B-c96ca--page-loads-and-shows-steps-retry1/error-context.md) | - main [ref=e3]: |
| [test-results/test_user_flows-Scenario-D-59d7f-kout-creates-Stripe-session/error-context.md](test-results/test_user_flows-Scenario-D-59d7f-kout-creates-Stripe-session/error-context.md) | - main [ref=e3]: |
| [test-results/test_user_flows-Scenario-D-59d7f-kout-creates-Stripe-session-retry1/error-context.md](test-results/test_user_flows-Scenario-D-59d7f-kout-creates-Stripe-session-retry1/error-context.md) | - main [ref=e3]: |
| [test-results/test_visual_snapshots-Visu-34594-arding-step-3---Sender-info/error-context.md](test-results/test_visual_snapshots-Visu-34594-arding-step-3---Sender-info/error-context.md) | - main [ref=e3]: |
| [test-results/test_visual_snapshots-Visu-34594-arding-step-3---Sender-info-retry1/error-context.md](test-results/test_visual_snapshots-Visu-34594-arding-step-3---Sender-info-retry1/error-context.md) | - main [ref=e3]: |
| [test-results/test_visual_snapshots-Visu-4d185-ews-10---Dashboard-overview/error-context.md](test-results/test_visual_snapshots-Visu-4d185-ews-10---Dashboard-overview/error-context.md) | - main [ref=e3]: |
| [test-results/test_visual_snapshots-Visu-6e2d6-ing-step-1---Connect-Google/error-context.md](test-results/test_visual_snapshots-Visu-6e2d6-ing-step-1---Connect-Google/error-context.md) | - main [ref=e3]: |
| [test-results/test_visual_snapshots-Visu-6e2d6-ing-step-1---Connect-Google-retry1/error-context.md](test-results/test_visual_snapshots-Visu-6e2d6-ing-step-1---Connect-Google-retry1/error-context.md) | - main [ref=e3]: |
| [test-results/test_visual_snapshots-Visu-98070-rding-step-2---Select-sheet/error-context.md](test-results/test_visual_snapshots-Visu-98070-rding-step-2---Select-sheet/error-context.md) | - main [ref=e3]: |
| [test-results/test_visual_snapshots-Visu-98070-rding-step-2---Select-sheet-retry1/error-context.md](test-results/test_visual_snapshots-Visu-98070-rding-step-2---Select-sheet-retry1/error-context.md) | - main [ref=e3]: |
| [test-results/test_visual_snapshots-Visu-a9750-oard-after-login-mock-auth-/error-context.md](test-results/test_visual_snapshots-Visu-a9750-oard-after-login-mock-auth-/error-context.md) | - main [ref=e3]: |
| [test-results/test_visual_snapshots-Visu-a9750-oard-after-login-mock-auth--retry1/error-context.md](test-results/test_visual_snapshots-Visu-a9750-oard-after-login-mock-auth--retry1/error-context.md) | - main [ref=e3]: |
| [uv.lock](uv.lock) | No description available. |
| [vercel.json](vercel.json) | No description available. |

<!-- LIBRARIAN-INDEX-END -->

## Recent Activity

- 2026-03-10: chore: fix broken Documents/ references after migration
- 2026-03-10: chore: migrate Documents/ to root and .agent/rules/ (smart-invoice-workflow)
- 2026-03-08: feat: Regenerate legal docs with Google API disclosure + expand E2E tests (#4812, #4778)
- 2026-03-01: feat: cinematic landing page redesign + production cleanup (#4968)
- 2026-03-01: fix: connect navbar anchor links to sections
- 2026-03-01: feat: implement high-fidelity cinematic landing page with refined protocol graphics
- 2026-03-01: test: add Playwright E2E tests for production smoke testing (#4778)
- 2026-02-28: docs: update ship checklist with verified steps 1-4, 7-9
- 2026-02-28: fix: use timezone-naive datetimes to match Neon DB schema
- 2026-02-27: feat: kill switch, daily cron trigger, deploy config, docs cleanup (#4953, #4960, #4945, #4823, #4779)
