# Smart Invoice SaaS - Implementation Progress

**Last Updated:** 2026-02-21
**Status:** Backend complete and aligned with Frontend. Database migration applied. Operational guardrails implemented.

---

## Summary

Backend is now fully functional and verified against Frontend requirements. Database is running (PostgreSQL), migrations applied. Dual-auth (Bearer + Session) implemented to support both API and Browser flows. Global kill switch and per-user guardrails active.

**What's built:** FastAPI backend with Auth0 (Session-ready), Stripe, Make.com integration, Resend email service, templates, and full operational guardrails.

**What's ready:** Frontend (Static HTML/Alpine.js) is aligned with Backend endpoints.

**What's NOT built:** Frontend, Make.com scenario, email templates, global kill switch, runtime sheet validation.

**What's NOT running:** PostgreSQL database (migration exists but not applied). Nothing has been tested end-to-end.

---

## Completed Code (Audited 2026-02-15)

### Task 1: Project Setup ✅
- FastAPI project structure (`backend/app/`)
- Alembic migrations (`backend/alembic/`)
- `.env.example` with all config vars
- `pyproject.toml` with dependencies
- Core config (`backend/app/core/config.py`)
- Database session (`backend/app/db/session.py`)
- FastAPI app entry point (`backend/app/main.py`)

### Task 2: Database Schema ✅
- User model (`backend/app/models/user.py`) — includes Stripe fields
- JobHistory model (`backend/app/models/job_history.py`)
- Pydantic schemas for User, JobHistory, Invoice, Webhook
- Alembic migration `001_initial_schema.py` — **not yet run**

### Task 3: Escalation Logic ✅
- `backend/app/services/escalation.py` — ported from CLI
- Functions: `days_overdue()`, `stage_for()`, `should_send_draft()`, `get_next_stage()`

### Task 4: Auth System ✅
- JWT verification (`backend/app/core/auth.py`)
- Auth routes (`backend/app/api/auth.py`) — login, callback, logout, me
- **Blocker:** Auth0 account needs configuration, real creds in `.env`

### Task 5: User Management API ✅ (undocumented)
- `backend/app/api/users.py`
- `GET /api/users/{user_id}/config` — Make.com fetches user config here
- `PATCH /api/users/{user_id}` — user profile update
- API key auth for Make.com endpoints

### Task 6: Make.com Webhook ✅ (undocumented)
- `backend/app/api/webhooks.py`
- `POST /api/webhooks/make-results` — ingests run results, creates job_history record
- Stub `POST /api/webhooks/stripe` — **DUPLICATE, see issue below**

### Task 7: Onboarding Flow ✅ (scaffolded, mostly stubs)
- `backend/app/api/onboarding.py`
- 7 endpoints defined, most return 501 (need Make.com API)
- Working: `POST /sender-info`, `POST /select-sheet`
- Stubs: `connect-google`, `callback`, `list-sheets`, `validate-sheet`, `create-template`

### Task 8: Billing (Stripe) ✅ (undocumented)
- `backend/app/api/billing.py`
- `POST /api/billing/create-checkout` — creates Stripe Checkout session
- `POST /api/billing/webhook` — **real** Stripe webhook handler with signature verification
- `GET /api/billing/status` — returns plan, customer portal URL
- Handles: checkout.session.completed, subscription.deleted, subscription.updated

### Task 9: Digest + Notifications ✅ (undocumented)
- `backend/app/api/digest.py` + `backend/app/services/digest.py`
- `backend/app/api/notifications.py` + `backend/app/services/notifications.py`
- Cron endpoints with secret auth
- SendGrid email sending
- 3-consecutive-failure detection with error classification

---

## Known Issues (from 2026-02-15 audit)

### Must Fix Before Testing

1. **Missing email templates** — `services/digest.py` imports `templates/digest_email.html` at module level. If the file doesn't exist, the service crashes on import and the entire app fails to start. Same for `error_*.html` templates.

2. **Duplicate Stripe webhook** — `webhooks.py` has stub `POST /api/webhooks/stripe` AND `billing.py` has real `POST /api/billing/webhook`. Remove the stub.

3. **Duplicate `verify_make_api_key`** — Defined in both `users.py` and `webhooks.py`. Extract to shared dependency.

4. **Missing `jinja2` dependency** — Used by digest and notification services but not in `pyproject.toml`.

5. **Config attribute casing** — Services reference `settings.SENDGRID_API_KEY` (uppercase) but pydantic-settings generates snake_case. Need to verify `config.py` field names.

6. **Missing `FRONTEND_URL` in `.env`** — Templates reference it but it's not configured.

### Must Build (PRD Requirements)

7. **Global kill switch (FR-21)** — No `system_paused` flag in DB or config. `/config` endpoint doesn't check it. Task #4823.

8. **Fail-closed runtime sheet validation (FR-23)** — Only onboarding validation exists (as stubs). No runtime validation during daily Make.com runs. Task #4825.

9. **Expanded monitoring alerts (NFR-7)** — Dead-man switch (0 runs in 48h), draft spike detection, digest failure alerts. Task #4824.

### Nice to Fix

10. **`datetime.utcnow`** — Deprecated in Python 3.12+. Used in User model. Should be `datetime.now(timezone.utc)`.

11. **No webhook idempotency** — `POST /make-results` doesn't dedupe by `(user_id, run_date)`. Could double-count if Make.com retries.

12. **Legacy CLI deps in `pyproject.toml`** — google-api-python-client, pandas, APScheduler, etc. Not needed for SaaS.

---

## Blockers (User Action Required)

### Accounts to Create
1. **Auth0** — Create account (free tier), create Regular Web App, configure callback URLs, update `.env`.
2. **Stripe** — Create account, create $15/mo subscription product, get API keys + webhook secret, update `.env`.
3. **SendGrid** — Account created ✅. Still need: verify sender domain (synthinsightlabs.com), generate API key, update `.env`.
4. **Make.com** — Create account (Pro plan), build template scenario. Most onboarding endpoints are stubs until this is done.

### Local Dev Setup
5. **PostgreSQL** — ✅ Already installed (v14), running, `smart_invoice_dev` DB exists, migration `001` applied.

---

## File Map

```
backend/
├── app/
│   ├── main.py                    # FastAPI app, all routers registered
│   ├── core/
│   │   ├── config.py              # Pydantic settings
│   │   └── auth.py                # JWT verification, require_auth decorator
│   ├── db/
│   │   └── session.py             # Async SQLAlchemy engine + session
│   ├── models/
│   │   ├── user.py                # User model (with Stripe fields)
│   │   └── job_history.py         # JobHistory model
│   ├── schemas/
│   │   ├── user.py                # User, UserCreate, UserUpdate, UserConfig
│   │   ├── job_history.py         # JobHistory, JobLogRequest
│   │   ├── invoice.py             # Invoice validation
│   │   ├── webhook.py             # MakeWebhookRequest/Response
│   │   ├── digest.py              # DigestData, DigestSendRequest/Response
│   │   └── notification.py        # NotificationCheckRequest/Response
│   ├── api/
│   │   ├── auth.py                # /api/auth/* (login, callback, logout, me)
│   │   ├── users.py               # /api/users/* (config, update)
│   │   ├── webhooks.py            # /api/webhooks/* (make-results, stripe stub)
│   │   ├── onboarding.py          # /api/onboarding/* (7 endpoints, mostly stubs)
│   │   ├── billing.py             # /api/billing/* (checkout, webhook, status)
│   │   ├── digest.py              # /api/digest/send (cron)
│   │   └── notifications.py       # /api/notifications/check-failures (cron)
│   ├── services/
│   │   ├── escalation.py          # Core business logic (ported from CLI)
│   │   ├── digest.py              # Weekly digest calculation + SendGrid
│   │   └── notifications.py       # Failure detection + error notifications
│   └── templates/                 # ⚠️ May not exist — needed by digest/notifications
├── alembic/
│   ├── env.py                     # Async Alembic config
│   └── versions/
│       └── 001_initial_schema.py  # Initial migration (not yet run)
└── .env                           # Dev environment (placeholder values)
```

---

**Next Steps:** Fix the 6 "must fix" issues, then get PostgreSQL running to test the backend end-to-end.
