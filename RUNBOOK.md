# Smart Invoice Workflow — Runbook (MVP)

This runbook is for **operating SIW safely** during MVP: diagnosing failures, preventing runaway behavior, and restoring service quickly.

---

## 0) First response: protect users + protect your day

### If anything seems wrong (draft spam, wrong emails, spikes)
1. **Enable Global Kill Switch** (pause all processing)
2. **Disable affected users** (`active=false`)
3. Confirm no new drafts are being created on the next scheduled run
4. Then troubleshoot.

**Principle:** Fail closed. It’s always better to pause than to create incorrect drafts.

---

## 1) System map (mental model)

- **Make.com** runs per-user scheduled scenarios:
  - First module: `GET /api/users/{user_id}/config`
  - Processing modules: read sheet, decide stage, create drafts, update stage
  - Last module: `POST /api/webhooks/make-results`
- **Backend** stores:
  - Users (plan, sheet_id, business/sender fields, active flag)
  - Job history (success/failure, drafts_created, totals)
- **Email**:
  - Drafts created via Gmail compose scope (no auto-send)
  - Weekly digest sent every Monday

---

## 2) Key controls (know these cold)

### 2.1 Global kill switch
**Use when:** draft spam risk, unknown behavior, widespread failures.
- Location: DB flag or env/config flag (document exact mechanism in your repo)
- Expected behavior:
  - `/config` returns `paused=true` (or similar)
  - Make scenario exits early and creates **zero** drafts

### 2.2 Per-user kill switch
**Use when:** single user misconfigured sheet, extreme draft volume, or complaint.
- Set `active=false` for that user (or equivalent)
- Confirm next run creates zero drafts for that user

### 2.3 Run caps
- Free: 3 overdue invoices per run
- Paid: enforce a sane per-run cap (e.g., 100) even if “unlimited” overall

---

## 3) Common incidents and how to fix them

### Incident A: Make scenario failing for a user (repeated failures)
**Symptoms**
- Job history shows failures; alert after 3 consecutive failures
- No new drafts created

**Likely causes**
- Google connection revoked/expired
- Sheet ID changed or access revoked
- Sheet format invalid (columns missing)
- Backend endpoint unreachable / returning non-200

**Steps**
1. Check Job history error payload (store Make error text if possible)
2. Verify user `active=true` and system not paused
3. Test backend endpoint:
   - `GET /api/users/{user_id}/config`
4. Confirm sheet access:
   - user still has sheet
   - correct permissions
5. If OAuth issue:
   - ask user to reconnect Google
6. If sheet format issue:
   - send template + instructions
   - keep user paused until fixed

**Restore**
- Run a manual scenario execution (or force a run) after fix
- Confirm drafts appear and webhook results recorded

---

### Incident B: Drafts being created repeatedly for the same invoices (duplicate drafts)
**Symptoms**
- User sees repeated drafts for same invoice(s)
- Draft count spikes

**Likely causes**
- Sheet stage tracking not updating
- Idempotency missing (same run executed multiple times)
- Make scenario retried after partial failure and re-drafted

**Steps**
1. Pause user (`active=false`) immediately
2. Inspect sheet stage-tracking columns:
   - did they update after draft creation?
3. Confirm Make scenario order:
   - draft creation should happen only when invoice is eligible *and* not already staged for today
4. Add/verify an idempotency key:
   - per invoice: `last_draft_date` or `last_stage_sent_date`
   - per run: `run_id` from Make (if available)
5. Ensure webhook ingestion is idempotent to avoid re-trigger logic

**Restore**
- Re-enable user
- Run once and verify no duplicates

---

### Incident C: Draft spam / too many drafts in a single run
**Symptoms**
- Unusually high drafts created
- User complains; or monitoring alert triggers

**Immediate action**
1. Enable global kill switch if more than one user affected
2. Otherwise disable only that user

**Likely causes**
- Missing run cap on paid plan
- Spreadsheet unexpectedly huge
- “Overdue” filter bug
- Misread columns (e.g., date parsing)

**Steps**
1. Confirm run caps enforced by `invoice_limit` from `/config`
2. Confirm Make scenario limits the row read to `invoice_limit`
3. Validate date parsing with a known test row
4. Add “sanity check” in Make:
   - if drafts_created > threshold, abort before creating drafts (or stop after N)

**Restore**
- Re-run with a capped sheet subset
- Resume cautiously

---

### Incident D: Backend endpoint errors (5xx / timeouts)
**Symptoms**
- Many Make scenarios failing at first module
- Spikes in failure alerts

**Likely causes**
- Deployment regression
- DB down or exhausted connections
- Misconfigured env vars

**Steps**
1. Enable global kill switch (optional; depends on partial behavior)
2. Check backend logs for `/config` and `/make-results`
3. Roll back to last known-good deployment if needed
4. Confirm DB connectivity and migrations

**Restore**
- Run smoke test user
- Resume processing

---

### Incident E: Stripe webhook / billing plan mismatch
**Symptoms**
- User paid but still limited to free tier
- User canceled but still treated as paid (or vice versa)

**Likely causes**
- Webhook not received / failed
- No idempotency on webhook handler
- Wrong environment keys (test vs prod)

**Steps**
1. Check Stripe dashboard events for the user
2. Check your webhook logs for the event ID
3. Verify webhook signing secret
4. Apply manual fix:
   - set user plan status in DB correctly
5. Make webhook handler idempotent:
   - dedupe by Stripe `event.id`

**Restore**
- Re-run `/config` to confirm plan
- Ask user to retry daily run

---

### Incident F: Weekly digest not sending
**Symptoms**
- Users don’t receive Monday digest
- Digest job missing or failing

**Likely causes**
- Scheduler misconfigured
- Email provider errors
- Job history missing data for aggregation

**Steps**
1. Confirm scheduler ran
2. Confirm email provider status
3. Verify digest query:
   - last 7 days job history aggregation per user
4. Retry digest job manually for one user

**Restore**
- Send a one-off digest if needed
- Fix scheduler

---

## 4) Support playbook (copy/paste)

### 4.1 “We paused your automation”
> We temporarily paused your invoice follow-ups to prevent incorrect drafts. Nothing was sent — drafts only. We’re fixing the issue now and will resume once it’s safe.

### 4.2 “Reconnect Google”
> It looks like your Google connection expired or was revoked. Please reconnect Google in the app, then we’ll resume your daily runs.

### 4.3 “Your sheet needs the template”
> Your spreadsheet is missing one or more required columns. Please copy your invoices into our template sheet (link), then re-select it in onboarding.

---

## 5) Operational hygiene (do this weekly)

- Review alerts and resolve any users with repeated failures
- Verify Make.com operations usage is within plan limits
- Review draft spike logs
- Confirm digest emails were sent Monday
- Run a full kill-switch drill monthly (practice)

---

## 6) Postmortem template (keep it short)

- What happened?
- Impact (how many users, drafts created, duration)
- Root cause
- Fix implemented
- Guardrail added (so it can’t happen again)
- Follow-up tasks (max 3)
