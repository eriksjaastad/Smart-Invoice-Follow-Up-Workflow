# Smart Invoice Workflow — Current State

**Last Updated:** 2026-03-16 1:30 PM

## What's Working
- Auth0 signup/login — WORKING
- Onboarding flow (sheet ID entry, sender info) — WORKING
- Stripe payment ($15/mo Pro plan) — WORKING
- Stripe webhook → plan upgrade — WORKING
- Daily cron trigger → Make.com webhook — WORKING
- Make.com reads Google Sheet — WORKING (after sharing with Make.com's Google account)
- Dashboard shows correct plan (Paid, 100 invoices/mo) — WORKING

## What We Just Fixed (March 16)
1. Auth0 callback URL was localhost → fixed to production URL
2. FRONTEND_URL and CORS_ORIGINS were localhost → fixed
3. Duplicate Vercel env vars (production-scoped vs all-environments) — learned to use `vercel env remove` not `rm`
4. www.smartinvoiceworkflow.com → was on dead Vercel project, moved to real project
5. Onboarding "Continue to Google" → was redirecting browser to Make.com webhook directly, skipped to Step 2
6. Cron was missing `x-make-apikey` header → added to cron.py
7. Cron was sending users without sheet_id → added filter
8. Sheet ID had trailing slash → added .rstrip("/") and fixed in app settings
9. Currency column in sheet was shifting columns → removed from test sheet
10. dateDiff unit was `F` instead of `"D"` → fixed in Make.com

## Current Blocker
- **Waiting to confirm**: Does the full Make.com pipeline complete? Last trigger sent successfully. Need to check Make.com logs for all-green and Gmail for new draft.

## Code Changes Made Today (not committed)
- `backend/app/api/cron.py` — added x-make-apikey header, spreadsheetId field, sheet_id filter, rstrip
- `backend/app/api/onboarding.py` — strip trailing slash from sheet_id
- `static/onboarding.html` — skip Google OAuth redirect, go straight to sheet ID entry

## Known Issues (not blocking launch)
- JWT_SECRET is still placeholder
- Google OAuth per-user not implemented (currently relies on Make.com's shared Google connection + sheet sharing)
- Create Template Make.com scenario is broken (addRow bug)
- Onboarding "Complete Setup" button stays active after completion (cosmetic)
- Second user in DB with no sheet_id (from earlier testing)

## Env Vars Fixed Today
| Variable | Fixed |
|----------|-------|
| AUTH0_CALLBACK_URL | https://smartinvoiceworkflow.com/api/auth/callback |
| FRONTEND_URL | https://smartinvoiceworkflow.com |
| CORS_ORIGINS | includes production domain |
| STRIPE_WEBHOOK_SECRET | real whsec_ value |
| X_MAKE_API_KEY | confirmed matching Make.com |

## Next Steps (in order)
1. Confirm Make.com pipeline completes end-to-end (check logs + Gmail)
2. Commit today's code changes
3. Set up Instantly.ai for cold email outreach
4. Distribution: Product Hunt, Reddit, Indie Hackers, LinkedIn
5. Fix Google OAuth for real customers (per-user tokens)
6. Switch Stripe to live keys when ready for real money
