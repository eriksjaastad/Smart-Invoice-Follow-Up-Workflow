# Smart Invoice Workflow — Launch Checklist (MVP)

**Scope reminder (MVP firewall):** Ship only what supports **sign up → connect Google → pick sheet → daily drafts → weekly digest → upgrade**. No admin panel, no settings, no extras.

---

## 0) Definitions

- **SIW** = Smart Invoice Workflow
- **Make scenario** = one cloned scenario per user (stores only `user_id`)
- **Backend** = source of truth for user config + plan limits
- **Digest day** = Monday
- **Kill switch** = ability to pause all processing immediately

---

## 1) Pre-launch prerequisites (must be true before inviting users)

### 1.1 Product / UX
- [ ] Landing page: clear one-liner + CTA (“Stop chasing invoices. We do it for you.”)
- [ ] Signup works (email/password or magic link) and creates user record
- [ ] Onboarding completes in < 2 minutes:
  - [ ] Connect Google via Make.com verified OAuth
  - [ ] Pick existing sheet OR create from template
  - [ ] Confirm “You’re live” screen

### 1.2 Template sheet + validation
- [ ] Template sheet exists and is selectable/creatable during onboarding
- [ ] Column validation runs at setup with *clear* errors (fail closed)
- [ ] “Bad sheet format” never triggers partial writes or draft creation

### 1.3 Core daily processing (end-to-end)
- [ ] Daily Make scenario run for a test user:
  - [ ] Reads sheet
  - [ ] Selects overdue invoices
  - [ ] Applies the 6-stage escalation logic (42 days, fixed)
  - [ ] Creates Gmail drafts (no auto-send)
  - [ ] Updates the sheet stage tracking
- [ ] Free tier enforcement works:
  - [ ] Max **3 overdue invoices** processed per daily run
  - [ ] UI shows upgrade prompt when limit reached (not silent)
- [ ] Paid tier works:
  - [ ] Unlimited invoices (still bounded by sanity caps per run; see Guardrails)
- [ ] Weekly digest email contents are correct:
  - [ ] Drafts created (weekly)
  - [ ] Total outstanding amount
  - [ ] Count of “critical” invoices (35+ days overdue)
  - [ ] “Go review Gmail drafts” prompt

### 1.4 Billing (Stripe)
- [ ] Stripe Checkout works: $15/month (and $120/year if enabled)
- [ ] Webhook updates user plan status correctly (no double-processing)
- [ ] Upgrade/downgrade behavior is clear:
  - [ ] Upgrade takes effect immediately for the next daily run
  - [ ] Cancel reverts to free tier at end of billing period (or your chosen rule, documented)

### 1.5 Backend endpoints (Make ↔ backend)
- [ ] `GET /api/users/{user_id}/config` returns:
  - [ ] `sheet_id`
  - [ ] `sender_name`
  - [ ] `business_name`
  - [ ] `plan`
  - [ ] `invoice_limit` (3 free, 100+ paid)
- [ ] `POST /api/webhooks/make-results` ingests:
  - [ ] `user_id`
  - [ ] `drafts_created`
  - [ ] `total_outstanding_amount`
  - [ ] (optional) `critical_count`
  - [ ] Saves job history record

### 1.6 Guardrails (non-negotiable)
**These prevent “ruin my day” incidents.**
- [ ] **Global kill switch** implemented (DB flag or env flag) and wired into:
  - [ ] `GET /config` (returns paused)
  - [ ] Make scenario “first module” checks paused and exits early
- [ ] **Per-user kill switch** (`active=false`) blocks processing
- [ ] **Hard caps per run**:
  - [ ] Free tier: `invoice_limit=3`
  - [ ] Paid tier: sane cap per run (e.g., 100) to prevent spreadsheet explosions
- [ ] **No parallel draft bursts** beyond a small per-user limit (serialize draft creation)
- [ ] **Idempotency**:
  - [ ] Webhook ingestion is idempotent (dedupe by `(user_id, run_id/date)`)

### 1.7 Monitoring + alerts
- [ ] Log every run with success/failure outcome in Job History
- [ ] Alert on **3 consecutive failures** per user
- [ ] Alert on **0 runs recorded in 48h** (system-level)
- [ ] Alert on **draft spike** anomaly (e.g., >X drafts/day/user)
- [ ] Digest send is logged; alert if digest job fails

### 1.8 Security / privacy
- [ ] Only request `gmail.compose` (drafts), not full Gmail read scope
- [ ] Do not store invoice line items on server (sheet is source of truth)
- [ ] Secrets stored correctly (env vars; no tokens in logs)

---

## 2) Test plan (run this checklist on staging, then on prod)

### 2.1 Golden path (Free)
- [ ] New user signs up → connects Google → selects template sheet
- [ ] Add 5 overdue invoices to sheet
- [ ] Run daily scenario
- [ ] Confirm:
  - [ ] Exactly 3 drafts created
  - [ ] Sheet updated for those 3
  - [ ] Upgrade prompt appears
  - [ ] Results webhook posted & stored

### 2.2 Golden path (Paid)
- [ ] Upgrade via Stripe
- [ ] Run daily scenario
- [ ] Confirm:
  - [ ] More than 3 drafts can be created (within per-run cap)
  - [ ] Plan reflected in `/config`

### 2.3 Failure modes (must fail closed)
- [ ] Sheet missing required column → no drafts created, clear error
- [ ] Google connection revoked → run logs failure + notifies user
- [ ] Backend down → Make scenario exits gracefully; logs failure
- [ ] Webhook post fails → run still creates drafts, but job history shows “results missing” and retries later (or logs to reconcile)

### 2.4 Kill switch drills
- [ ] Toggle global kill switch ON → next run creates **zero** drafts
- [ ] Toggle user `active=false` → next run creates **zero** drafts
- [ ] Toggle OFF → system resumes normally

---

## 3) Launch day steps (production)

### 3.1 Deploy
- [ ] Deploy backend + frontend
- [ ] Confirm env vars correct in production
- [ ] Confirm domain + DNS + SSL are correct
- [ ] Confirm Stripe prod keys + webhook endpoints

### 3.2 Smoke test (prod)
- [ ] Create a fresh prod test user
- [ ] Complete onboarding end-to-end
- [ ] Trigger one daily run manually (or wait for schedule)
- [ ] Confirm drafts appear in Gmail (as drafts)
- [ ] Confirm job history saved
- [ ] Confirm digest scheduler ready (Monday)

### 3.3 Monitoring live
- [ ] Confirm logs are streaming
- [ ] Confirm alert channels work (email/SMS/Push)
- [ ] Confirm kill switch is one-click available

### 3.4 Invite first users
- [ ] Start with 3–5 hand-held users (concierge onboarding)
- [ ] Watch their first daily run
- [ ] Collect one “confusion point” note per user
- [ ] Fix only *blocking* UX bugs (firewall!)

---

## 4) Post-ship (exactly 2 days)

### 4.1 Distribution sprint (2 days hard cap)
- [ ] Product Hunt post
- [ ] Reddit: r/smallbusiness, r/freelance, r/entrepreneur, r/SaaS
- [ ] Indie Hackers build-in-public
- [ ] LinkedIn personal + company
- [ ] Twitter/X company
- [ ] Facebook groups (if relevant)

### 4.2 Metrics to track daily (simple)
- [ ] New signups
- [ ] Activated users (completed onboarding)
- [ ] Drafts created per active user
- [ ] Upgrades to paid
- [ ] Support emails / failure alerts count

### 4.3 “Do not do” list (protect focus)
- [ ] No dashboard
- [ ] No new features unless they unblock onboarding or prevent failures
- [ ] No scope creep beyond the PRD firewall

---

## 5) Rollback plan (when something goes sideways)

- [ ] **Step 1:** Turn ON global kill switch (stop all drafts)
- [ ] **Step 2:** Post a status email to affected users (“Paused to prevent incorrect drafts; we’ll resume shortly.”)
- [ ] **Step 3:** Fix root cause
- [ ] **Step 4:** Run 1–2 test users in prod
- [ ] **Step 5:** Resume processing (kill switch OFF)
