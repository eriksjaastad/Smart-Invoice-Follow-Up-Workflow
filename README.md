<!-- SCAFFOLD:START - Do not edit between markers -->
# smart-invoice-workflow

Hosted SaaS that automates invoice follow-up for small businesses.

<!-- SCAFFOLD:END - Custom content below is preserved -->

## What This Is

**"Stop chasing invoices. We do it for you."**

Smart Invoice Workflow is a hosted SaaS by Synth Insight Labs. Users sign up, connect Google through Make.com's verified OAuth, pick their invoice spreadsheet, and the system creates Gmail drafts with escalating payment reminders on a 42-day, 6-stage schedule. Weekly digest emails prove the system is working.

- **Free tier:** 3 invoices/day
- **Paid tier:** 100 invoices/day, $15/month via Stripe

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLAlchemy (async PostgreSQL) |
| Frontend | Static HTML + Alpine.js (Vercel) |
| Auth | Auth0 (Universal Login) |
| Automation | Make.com Pro ($16/mo, 10K ops) |
| Payments | Stripe Checkout |
| Email | SendGrid (digests + notifications) |
| Hosting | Vercel (serverless) |

## Architecture

Make.com runs daily per user. Our backend is the brain — Make.com calls `GET /api/users/{id}/config` to get everything it needs (sheet_id, sender info, plan, invoice_limit), does the Google Sheets/Gmail work, then reports results via `POST /api/webhooks/make-results`.

No Google tokens touch our servers. Make.com handles OAuth.

## Directory Map

### Decision & Planning Docs
| File | Purpose |
|------|---------|
| `PRD.md` | Product Requirements Document (source of truth) |
| `PROPOSAL_FINAL.md` | Traceability matrix: PRD → Kiro specs |
| `DECISIONS.md` | Architectural Decision Records |
| `IMPLEMENTATION_PROGRESS.md` | Live build tracker (what's done, what's not) |
| `LAUNCH_CHECKLIST.md` | Pre-launch gates |
| `RUNBOOK.md` | Operations manual (kill switch, troubleshooting) |

### Code
| Directory | Purpose |
|-----------|---------|
| `backend/` | FastAPI app (models, schemas, services, API routes, Alembic migrations) |
| `static/` | Frontend HTML pages (index, login, onboarding, dashboard, billing, settings) |
| `src/` | Legacy Python CLI (pre-SaaS, kept for reference) |
| `scripts/` | Utility scripts |
| `tests/` | Test suite |

### Research & Sales
| Directory | Purpose |
|-----------|---------|
| `case-studies/` | Business research, pricing analysis, distribution strategy |
| `.agent/rules/FIRST_SALE_GUIDE.md` | How to make the first $5 |
| `.agent/rules/SALES_STRATEGY.md` | Comprehensive sales playbook |
| `../.agent/rules/GOOGLE_SHEET_TEMPLATE.md` | Invoice sheet column spec |

### Governance (Synced — Do Not Edit)
| File | Purpose |
|------|---------|
| `AGENTS.md` | Agent hierarchy and Dispatch Protocol |
| `CLAUDE.md` | Execution rules (synced via agentsync) |
| `.agent/rules/governance.md` | Review checklist (synced via sync_governance.py) |

### Kiro Specs
| File | Purpose |
|------|---------|
| `.kiro/specs/smart-invoice/requirements.md` | Functional requirements (EARS format) |
| `.kiro/specs/smart-invoice/design.md` | Technical design |
| `.kiro/specs/smart-invoice/tasks.md` | Implementation task breakdown |

## Status

**Phase:** Active development (backend built, frontend in progress)
**Goal:** Ship MVP, get one paying customer, learn to sell.

## CI / Automated Code Review

Pull requests are automatically reviewed by Claude Sonnet via a [centralized reusable workflow](https://github.com/eriksjaastad/tools/blob/main/.github/workflows/claude-review-reusable.yml) hosted in the `tools` repo.

**On every PR:**
- Tests run (if any exist)
- AI reviews the diff against project standards and governance protocol
- Posts a sticky review comment and a `claude-review` commit status
- Auto-merges on APPROVE, blocks on REQUEST_CHANGES

See [tools repo](https://github.com/eriksjaastad/tools) for configuration details.
