# Ship Checklist — Smart Invoice Workflow

**Last Updated:** 2026-02-27
**Ship Target:** March 7, 2026
**Domain:** https://smartinvoiceworkflow.com

---

## How This System Works (End-to-End)

```
Vercel cron (daily)
  → POST /api/cron/trigger-daily (our backend)
    → For each active user:
      → POST to Make.com Daily Processing webhook (with user config + backend_url)
        → Make.com reads Google Sheet
        → Make.com creates Gmail drafts for overdue invoices
        → Make.com POSTs results back to https://smartinvoiceworkflow.com/api/webhooks/make-results
          → Backend logs results in job_history table
```

---

## Database (Neon Postgres)

| Check | Status | Date |
|-------|--------|------|
| Migration 001 (users + job_history) | DONE | pre-2026-02-27 |
| Migration 002 (system_state / kill switch) | DONE | 2026-02-27 |
| system_state seeded (paused=false) | DONE | 2026-02-27 |
| Users table: 0 rows (expected) | VERIFIED | 2026-02-27 |

---

## External Accounts

| Service | Account | Status | Notes |
|---------|---------|--------|-------|
| Auth0 | Synth Insight Labs | DONE | Callback URLs need to match Vercel domain |
| Stripe | Synth Insight Labs | DONE | $15/mo product created |
| Resend | Synth Insight Labs | DONE | Sender domain: send.synthinsightlabs.com |
| Make.com | Synth Insight Labs | DONE | Pro plan, 4 webhooks active |
| Neon | — | DONE | Free tier, 3 tables |
| Vercel | — | DONE | Domain: smartinvoiceworkflow.com |

---

## Make.com Webhooks

| Scenario | Status | Webhook URL |
|----------|--------|-------------|
| Daily Processing | ACTIVE | hook.us2.make.com/sis5v... |
| List Sheets | ACTIVE | hook.us2.make.com/5s6h... |
| Validate Sheet | ACTIVE | hook.us2.make.com/v9oz... |
| Create Template | BROKEN | hook.us2.make.com/83d7... (addRow bug) |

**Make.com scenarios are currently OFF.** Do not turn on until backend deploy is verified.

---

## ENV Variables (.env)

| Variable | Set? | Notes |
|----------|------|-------|
| DATABASE_URL | YES | Neon connection string |
| AUTH0_DOMAIN | YES | |
| AUTH0_CLIENT_ID | YES | |
| AUTH0_CLIENT_SECRET | YES | |
| STRIPE_SECRET_KEY | YES | |
| STRIPE_WEBHOOK_SECRET | YES | |
| STRIPE_PRICE_ID | YES | |
| MAKE_DAILY_PROCESSING_WEBHOOK_URL | YES | Set in .env and Vercel |
| MAKE_LIST_SHEETS_WEBHOOK_URL | YES | Set in .env and Vercel |
| MAKE_VALIDATE_SHEET_WEBHOOK_URL | YES | Set in .env and Vercel |
| MAKE_CREATE_TEMPLATE_WEBHOOK_URL | YES | Set in .env and Vercel |
| X_MAKE_API_KEY | YES | Set in .env and Vercel |
| BACKEND_URL | YES | https://smartinvoiceworkflow.com |
| RESEND_API_KEY | YES | |
| RESEND_FROM_EMAIL | YES | noreply@send.synthinsightlabs.com |
| FRONTEND_URL | YES | https://smartinvoiceworkflow.com |
| DIGEST_CRON_SECRET | YES | Set in .env and Vercel |
| SYSTEM_CONTROL_SECRET | YES | Set in .env and Vercel |
| AUTH0_CALLBACK_URL | **FIX** | Still localhost — must be production URL |
| JWT_SECRET | **FIX** | Still placeholder — generate real secret |
| STRIPE_WEBHOOK_SECRET | **FIX** | Placeholder — need to create webhook endpoint first (see Step 9) |
| STRIPE_SECRET_KEY | NOTE | Test key (`sk_test_`) — switch to live key before real launch |
| STRIPE_PUBLISHABLE_KEY | NOTE | Test key (`pk_test_`) — switch to live key before real launch |
| CORS_ORIGINS | **FIX** | Still localhost — must include production domain |
| ENVIRONMENT | **FIX** | Still `development` — change to `production` |
| DEBUG | **FIX** | Still `true` — change to `false` |

**IMPORTANT:** These env vars must also be set in **Vercel Environment Variables** (Project Settings → Environment Variables). Local .env only works for local dev.

---

## Credential Rotation (Quarterly)

**Goal:** Reduce risk from long-lived tokens. Rotate every 90 days.

- [ ] Set calendar reminder: "Rotate SIW tokens (Vercel + Make.com)" every 90 days
- [ ] Rotate Vercel token (used for deploy tooling)
- [ ] Rotate Make.com API key / webhook auth key (`X_MAKE_API_KEY`)
- [ ] Update .env and Vercel env vars after rotation
- [ ] Record rotation date here (fill in):
- [ ] Vercel token rotated: __________
- [ ] Make.com API key rotated: __________

---

## Ship Sequence (Do In This Order)

### Step 1: Push code to git → Vercel deploys
- [x] `git push origin main` — DONE 2026-02-28
- [x] Verify build succeeds on Vercel dashboard — DONE 2026-02-28
- [x] Hit https://smartinvoiceworkflow.com/health — returns JSON — DONE 2026-02-28
- **NOTE:** Domain was on wrong Vercel project (`smartinvoiceworkflow` vs `smart-invoice-workflow`). Fixed 2026-02-28.
- **NOTE:** No GitHub integration on this project. Deploys via `vercel --prod` CLI.

### Step 2: Verify Vercel env vars
- [x] All 24 env vars set in Vercel project settings — VERIFIED 2026-02-28
- [x] BACKEND_URL = https://smartinvoiceworkflow.com — VERIFIED
- [x] MAKE_DAILY_PROCESSING_WEBHOOK_URL is set — VERIFIED
- [x] Redeployed after adding BACKEND_URL and SYSTEM_CONTROL_SECRET — DONE 2026-02-28

### Step 3: Verify backend endpoints
- [x] GET https://smartinvoiceworkflow.com/health → 200 — DONE 2026-02-28
- [x] GET https://smartinvoiceworkflow.com/api/system/status → {"paused": false} — DONE 2026-02-28
- [x] Landing page loads at https://smartinvoiceworkflow.com/ → 200 — DONE 2026-02-28

### Step 4: Test Make.com connection
- [x] curl POST to /api/cron/trigger-daily with cron secret → `{"success":true,"users_total":0,"sent":0}` — DONE 2026-02-28
- [x] Make.com scenarios are OFF (correct — don't turn on until Step 10)

### Step 5: Test signup flow (first real user = you)
- [ ] Sign up via Auth0
- [ ] Connect Google Sheet
- [ ] Verify user appears in Neon users table
- [ ] Manually trigger daily processing
- [ ] Check Gmail for draft emails
- [ ] Check job_history table for results

### Step 6: Test payment
- [ ] Use Stripe test card (4242 4242 4242 4242)
- [ ] Verify plan changes from "free" to "paid" in DB
- [ ] Verify invoice_limit changes from 3 to 100

### Step 7: Test kill switch
- [x] POST /api/system/pause with secret → `{"paused":true}` — DONE 2026-02-28
- [x] Verified status endpoint returns paused=true — DONE 2026-02-28
- [x] POST /api/system/pause → `{"paused":false}` (re-enabled) — DONE 2026-02-28
- **BUG FIXED:** 500 error on pause was caused by timezone-aware datetimes vs tz-naive DB columns. Fixed in commit 3ca4196.

### Step 8: Set up Vercel cron (daily trigger)
- [x] Cron job in vercel.json: `0 15 * * *` (daily at 3PM UTC / 10AM EST) — DONE
- [ ] Verify it runs next day (check tomorrow)

### Step 9: Production hardening (env vars)
- [x] `AUTH0_CALLBACK_URL` → `https://smartinvoiceworkflow.com/api/auth/callback` — DONE 2026-02-27
- [x] `JWT_SECRET` → generate real secret — DONE 2026-02-27
- [x] `CORS_ORIGINS` → add `https://smartinvoiceworkflow.com` — DONE 2026-02-27
- [x] `SYSTEM_CONTROL_SECRET` → generate real secret — DONE 2026-02-27
- [x] `STRIPE_WEBHOOK_SECRET` → create Stripe webhook endpoint, then grab `whsec_` secret — DONE 2026-02-28
  - Endpoint ID: `we_1T5rCIJeImVkp02DzhZ3iheP`
  - Endpoint URL: `https://smartinvoiceworkflow.com/api/billing/webhook`
  - Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`
  - Mode: Test (livemode: false)
  - **Stripe CLI installed** (`stripe` v1.37.1) — DONE 2026-02-27
- [ ] Switch Stripe keys from test (`sk_test_`/`pk_test_`) to live before real launch
- [x] `ENVIRONMENT` → `production` — already set in Vercel — VERIFIED 2026-02-28
- [ ] `DEBUG` → `false` (intentionally left as `true` until all testing complete)
- [x] `GMAIL_SENDER` → NOT USED in codebase, legacy only — VERIFIED 2026-02-28
- [x] All env vars verified in Vercel, redeployed — DONE 2026-02-28

### Step 10: Ship
- [ ] All steps above green
- [ ] Turn on Make.com scenarios (Daily Processing, List Sheets, Validate Sheet)
- [ ] Monitor first real daily run

### Step 11: Distribution (2 days max, then stop)
- [ ] Product Hunt
- [ ] Reddit (r/SideProject, r/EntrepreneurRideAlong)
- [ ] Indie Hackers
- [ ] LinkedIn
- [ ] Twitter/X

---

## Known Issues

| Issue | Card | Impact |
|-------|------|--------|
| Create Template scenario broken (addRow bug) | #4943 | Users can't auto-create template sheets. Workaround: manually create sheet. |
| Legal (ToS/Privacy) not done | #4812 | Must complete before public launch |
| Product name research not done | #4811 | Low risk, do before distribution |
| Make.com pricing model not validated | #4810 | Need to verify free tier is sustainable |

---

## Legal Docs (Drafts)

- [ ] Review and finalize Terms of Service draft:
[Terms of Service](Documents/legal/TERMS_OF_SERVICE.md)
- [ ] Review and finalize Privacy Policy draft:
[Privacy Policy](Documents/legal/PRIVACY_POLICY.md)
- [ ] Use a generator to finalize language and confirm required clauses:
Termly, TermsFeed, or iubenda
- [ ] Publish final versions to the site footer and link on signup page

---

## If You're Reading This Monday Morning

1. **Where we left off:** Migration 002 applied. Code ready to push. Vercel env vars need checking.
2. **Next action:** Step 1 above — push to git, verify Vercel build.
3. **Floor Manager status:** Was working on tasks, check kanban for updates.
4. **Make.com scenarios:** OFF. Don't turn on until Step 4 is complete.
