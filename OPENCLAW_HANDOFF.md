# OpenClaw Handoff — Smart Invoice Workflow

**Date:** 2026-03-25
**From:** Erik + Claude Code (Architect)
**To:** OpenClaw (DVF Distribution)
**Goal:** First paying stranger. One dollar.

---

## What This Product Does

Automated invoice follow-up for freelancers and micro-agencies who track invoices in Google Sheets.

User connects their Google account, points to their spreadsheet, and the system creates escalating Gmail draft reminders over 42 days (6 stages: friendly → firm → final notice). User reviews and sends the drafts manually — we never send on their behalf.

**Live at:** https://smartinvoiceworkflow.com

---

## What Works

- Auth0 login (Google social login)
- Google OAuth connection (Sheets + Gmail access)
- Onboarding: connect Google → paste sheet URL → set sender info
- Daily cron processing: reads sheet, finds overdue invoices, creates Gmail drafts, updates sheet
- 6-stage escalation templates (7/14/21/28/35/42 days overdue)
- Stripe checkout: free → paid upgrade via webhook
- 102 Playwright E2E tests passing against production
- Free tier: 3 invoices/day, Paid tier: 100 invoices/day

## What You Have Authority Over

- **Pricing** — currently $15/month. We suggest $9/month. Your call entirely.
- **Distribution channels** — Reddit, Product Hunt, Indie Hackers, SEO, cold outreach, whatever works
- **Content and messaging** — landing page copy, marketing materials, positioning
- **Free tier limits** — currently 3 invoices/day on free plan. Adjust if needed.

---

## Tech Stack

| Layer | Service | Account |
|-------|---------|---------|
| Frontend | Static HTML + Tailwind + Alpine.js | Vercel (deploys on push to main) |
| Backend | FastAPI (Python) on Vercel serverless | Same Vercel project |
| Database | Neon Postgres | Connected via DATABASE_URL |
| Auth | Auth0 | Synth Insight Labs tenant |
| Payments | Stripe (test mode keys currently) | Synth Insight Labs account |
| Email | Gmail API (per-user OAuth) | User's own Google account |
| DNS | smartinvoiceworkflow.com | Namecheap → Vercel nameservers |
| Secrets | Doppler | Project: smart-invoice-workflow |

## Env Vars (all in Doppler + Vercel)

```
AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_DOMAIN, AUTH0_CALLBACK_URL
STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_ID
GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, GOOGLE_TOKEN_ENCRYPTION_KEY
DATABASE_URL, SECRET_KEY, DIGEST_CRON_SECRET
FRONTEND_URL=https://smartinvoiceworkflow.com
```

---

## What We Know

1. **The product works end-to-end.** We ran escalation tests with 18 edge-case invoice rows and verified Gmail drafts were created correctly for all 6 stages.

2. **Nobody else targets this niche.** Competitors either want users to migrate to their platform ($17-49/month) or are full AR automation suites ($200+/month). Nobody says "keep your Google Sheets, we just add the follow-ups."

3. **The target audience is freelancers who use Google Sheets for invoicing.** They hang out on r/freelance, r/smallbusiness, Indie Hackers, freelancer Facebook groups, and Slack communities.

4. **Paid ads won't work with a small budget.** Google Ads CPC for SaaS is $4-6/click. At 3-5% conversion, you need $200-500 to acquire one customer. Organic channels first.

5. **$9/month is the impulse-buy price point.** $15 is defensible but tight — users compare against FreshBooks at $17 which gives full invoicing. $9 is clearly in "just try it" territory.

6. **54% of freelancers experience delayed payments quarterly.** The pain is real and well-documented on Reddit. Common advice is manual follow-up processes — nobody recommends an automated tool for spreadsheet users.

## What We Don't Know

1. **Will anyone actually pay?** Product works, but zero strangers have used it. No market validation yet.

2. **Is the onboarding flow smooth enough?** Google OAuth consent screen can be intimidating. Users need to trust us with Gmail access. We haven't watched a stranger go through it.

3. **What happens at scale?** Google Sheets API has rate limits (100 req/100sec per user). With many users, we might need throttling. Vercel serverless has cold start latency.

4. **Is the landing page converting?** It looks good but has never been A/B tested. No analytics installed.

5. **Do we need to change the name?** "Smart Invoice" is heavily saturated. 6+ existing products. We own smartinvoiceworkflow.com but a rebrand might be needed.

6. **Legal gaps.** ToS and Privacy Policy have gaps (missing Google API Limited Use disclosure). Gmail compose is a restricted scope — needs Google verification ($15K-75K) at scale. Fine for <100 users in Testing mode.

7. **Stripe is in test mode.** The keys in production are test keys. Need to switch to live mode before real charges. This is a Stripe Dashboard toggle + updating the env vars.

---

## Known Bugs / Tech Debt

| Issue | Status | Impact |
|-------|--------|--------|
| Draft limit was not enforced (free plan) | FIXED — merged PR #6 | Was creating unlimited drafts on free tier |
| `sheet_id` stored as full URL sometimes | Workaround in `select-sheet` endpoint | Parses URL to extract ID, but old data may have full URLs |
| `datetime.utcnow()` deprecated | Minor | Python 3.12+ warning, should use `datetime.now(timezone.utc)` |
| No rate limiting on cron endpoint | Minor | 20 rapid hits all return 200. Fine for now, add rate limiting before scale |
| Google Drive MCP can't read/write sheets | Anthropic bug | Use picker-config token workaround for test scripts |

## Remaining Kanban Cards

```
#5277 — Free tier implementation (verify signup without Stripe works e2e)
#5278 — OpenClaw handoff (this document)
#5279 — Consider price drop to $9/month
#5132 — Accept full Google Sheets URL in onboarding (partially done)
#5266 — Replace Google Picker with paste-URL input (partially done)
#5264 — Column mapping for user-provided spreadsheets
#4825 — Fail-closed sheet validation
#4824 — Expanded monitoring alerts
#4780 — Distribution (2 days max)
```

---

## How to Run Tests

```bash
# No-auth tests (always work, no setup needed)
npx playwright test tests/e2e/test_no_auth.spec.js

# Auth setup (one-time, manual Auth0 login, saves session for 7 days)
npx playwright test tests/e2e/auth-setup.spec.js --headed

# Authenticated tests
npx playwright test tests/e2e/test_authenticated.spec.js

# Sheet + escalation tests (need DIGEST_CRON_SECRET)
DIGEST_CRON_SECRET=<from Doppler> npx playwright test tests/e2e/test_sheet_stress.spec.js

# Stripe lifecycle (need Stripe CLI authenticated)
npx playwright test tests/e2e/test_stripe_lifecycle.spec.js

# Everything
DIGEST_CRON_SECRET=<from Doppler> npx playwright test tests/e2e/
```

## How to Deploy

Push to main. Vercel auto-deploys.

## How to Upgrade a User to Paid (without checkout)

```bash
stripe trigger checkout.session.completed \
  --override checkout_session:metadata.user_id=<USER_UUID>
```

---

## When You Need Erik

- **Google Cloud Console changes** — adding test users, changing OAuth scopes, enabling APIs
- **Stripe live mode switch** — he has the Stripe Dashboard access
- **Auth0 tenant changes** — adding allowed callback URLs, changing settings
- **Domain/DNS changes** — Namecheap access
- **Doppler secrets** — adding/changing env vars

For everything else — code changes, distribution, pricing, content, outreach — you have full authority. Make decisions, move fast, report results.

---

## Success Metric

One stranger pays. That's it. Everything else is secondary.
