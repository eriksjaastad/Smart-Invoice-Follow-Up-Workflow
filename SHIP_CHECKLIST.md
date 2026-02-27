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
| MAKE_DAILY_PROCESSING_WEBHOOK_URL | CHECK | Needs the webhook URL from Make.com |
| MAKE_LIST_SHEETS_WEBHOOK_URL | CHECK | |
| MAKE_VALIDATE_SHEET_WEBHOOK_URL | CHECK | |
| MAKE_CREATE_TEMPLATE_WEBHOOK_URL | CHECK | |
| X_MAKE_API_KEY | CHECK | |
| BACKEND_URL | YES | https://smartinvoiceworkflow.com |
| RESEND_API_KEY | YES | |
| RESEND_FROM_EMAIL | YES | noreply@send.synthinsightlabs.com |
| FRONTEND_URL | CHECK | Should be https://smartinvoiceworkflow.com |
| DIGEST_CRON_SECRET | CHECK | Needed for cron trigger auth |
| SYSTEM_CONTROL_SECRET | CHECK | Needed for kill switch API |

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
- [ ] `git push origin main`
- [ ] Verify build succeeds on Vercel dashboard
- [ ] Hit https://smartinvoiceworkflow.com/api/health — should return JSON

### Step 2: Verify Vercel env vars
- [ ] All env vars from table above are set in Vercel project settings
- [ ] BACKEND_URL = https://smartinvoiceworkflow.com
- [ ] MAKE_DAILY_PROCESSING_WEBHOOK_URL is set
- [ ] Redeploy if you added env vars after the build

### Step 3: Verify backend endpoints
- [ ] GET https://smartinvoiceworkflow.com/api/health → 200
- [ ] GET https://smartinvoiceworkflow.com/api/system/status → {"paused": false}
- [ ] Landing page loads at https://smartinvoiceworkflow.com/

### Step 4: Test Make.com connection
- [ ] curl POST to /api/cron/trigger-daily with cron secret (will return 0 users sent, which is correct — no users yet)
- [ ] Verify Make.com Daily Processing scenario received nothing (because 0 users)

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
- [ ] POST /api/system/pause with secret → paused=true
- [ ] Trigger daily processing → Make.com should skip all users
- [ ] POST /api/system/pause → paused=false (re-enable)

### Step 8: Set up Vercel cron (daily trigger)
- [ ] Add cron job in vercel.json that hits /api/cron/trigger-daily daily
- [ ] Verify it runs next day

### Step 9: Ship
- [ ] All steps above green
- [ ] Turn on Make.com scenarios (Daily Processing, List Sheets, Validate Sheet)
- [ ] Monitor first real daily run

### Step 10: Distribution (2 days max, then stop)
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

## If You're Reading This Monday Morning

1. **Where we left off:** Migration 002 applied. Code ready to push. Vercel env vars need checking.
2. **Next action:** Step 1 above — push to git, verify Vercel build.
3. **Floor Manager status:** Was working on tasks, check kanban for updates.
4. **Make.com scenarios:** OFF. Don't turn on until Step 4 is complete.
