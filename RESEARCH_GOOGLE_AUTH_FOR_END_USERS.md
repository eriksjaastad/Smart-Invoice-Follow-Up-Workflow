# Research Brief: Google OAuth for SIW End Users

**Date:** 2026-03-17
**Priority:** Critical — this is a blocking architectural decision
**Context:** Smart Invoice Workflow (SIW) is a hosted SaaS that reads users' Google Sheets and creates Gmail drafts on their behalf. The product works end-to-end but has a fatal onboarding flaw: there is no viable path for end users to authorize Google access.

---

## The Problem

SIW needs two Google OAuth scopes per user:
- `https://www.googleapis.com/auth/spreadsheets` — read/write their invoice spreadsheet
- `https://www.googleapis.com/auth/gmail.compose` (or `gmail.modify`) — create draft emails in their Gmail

The original architecture (designed Feb 2026) assumed Make.com could handle per-user Google OAuth on behalf of end users who do NOT have Make.com accounts. This assumption was wrong.

---

## What We Already Know (DO NOT RE-RESEARCH THESE)

### 1. Make.com's Credential Request API Does NOT Work for End Users

We tested `credential_requests_create` via the Make.com API. It returns a `publicUri`:
```
https://us2.make.com/1899817/credentials-requests/inbox?requestId=2a7a6918-a3d4-4a5c-873f-fec74565408e
```

**Result:** This URL redirects to a Make.com sign-up page. It is designed for Make.com team members to authorize connections, NOT for external end users of a SaaS product. This approach is dead.

### 2. Make.com Connections Are Hardcoded Per-Scenario

In Make.com blueprints, Google connections are set via `__IMTCONN__` parameter with a fixed connection ID (e.g., `7471828`). You cannot dynamically swap connections at runtime. This means:
- You can't have one scenario serve multiple users with different Google accounts
- Per-user scenarios require per-user connections
- Per-user connections require Make.com accounts (see point 1)

### 3. Current Working State

The product currently works with a **single shared Google connection** (admin@synthinsightlabs.com). The daily cron triggers a Make.com webhook per user, passing their config. Make.com reads their sheet using the shared connection. This requires users to manually share their Google Sheet with the admin account — which is unacceptable UX.

**Make.com connections currently in use:**
- Connection 7471828: "My Google connection" (google-sheets, admin@synthinsightlabs.com)
- Connection 7471878: "My Gmail connection" (google-email, admin@synthinsightlabs.com)
- Connection 7506553: "My Google Restricted connection" (google-restricted, admin@synthinsightlabs.com)

**Make.com scenarios:**
- Daily Processing (4171146) — reads sheet, creates drafts, updates rows
- Create Template (4198758) — creates new sheet from template
- List Sheets (4191896) — lists user's sheets
- Validate Sheet (4198721) — validates column structure

### 4. Google Verification Requirements

Per Google's documentation (as understood):
- Apps with <100 users may not need full verification
- Unverified apps show a warning screen ("This app isn't verified") but users can click through via "Advanced" → "Go to [app name] (unsafe)"
- Full verification requires: privacy policy, homepage verification, and a review process that takes 4-6 weeks
- Sensitive scopes (like gmail.modify) may have additional requirements

### 5. The Original PRD Design (Now Known to Be Flawed)

From PRD.md:
- FR-2: "Users connect their Google account through Make.com's verified OAuth integration"
- FR-3: "Make.com handles Google token storage and refresh — we never touch Google OAuth tokens directly"
- Data model includes `make_scenario_id` per user (for cloned scenarios)
- Architecture: "POST /scenarios/{id}/clone → set one build variable (user_id) → activate schedule → done"

This design assumed Make.com could mediate Google OAuth for non-Make.com users. It cannot.

---

## What We Need Researched

### A. Google OAuth Direct Implementation — Feasibility & Verification Requirements

1. **Exactly what does the "unverified app" experience look like in 2026?** Screenshots or detailed description of the click-through flow. How many clicks? What does the warning say? Would a non-technical small business owner (our target user) be scared off?

2. **What are the EXACT current requirements for Google OAuth app verification in 2026?** Specifically for these scopes:
   - `https://www.googleapis.com/auth/spreadsheets`
   - `https://www.googleapis.com/auth/gmail.compose` OR `https://www.googleapis.com/auth/gmail.modify`
   - Are these considered "sensitive" or "restricted" scopes?
   - What's the difference in verification requirements between sensitive and restricted?

3. **Is there a threshold (e.g., <100 users) where verification is not required?** What exactly happens when you exceed it? Does Google block new authorizations or revoke existing ones?

4. **How long does verification actually take in 2026?** Any recent data points from developers who've gone through it?

5. **What are the alternatives to full verification?** For example:
   - Google Workspace Marketplace apps
   - Google Workspace add-ons
   - Using a service account with domain-wide delegation (for Workspace users)
   - Google Cloud project set to "internal" (only works for same-org users)

### B. Make.com Embedded/White-Label OAuth

6. **Does Make.com have any embedded, white-label, or partner OAuth flow?** Something that lets a SaaS product use Make.com's verified Google OAuth without users needing Make.com accounts? Check:
   - Make.com Partner program
   - Make.com Embed SDK
   - Make.com "Connect on behalf of" features
   - Any Make.com documentation about building SaaS products on top of Make.com
   - Make.com's "Custom Apps" or "Custom Connections" features

7. **Has anyone built a SaaS product that uses Make.com for Google OAuth on behalf of end users?** Look for:
   - Blog posts, tutorials, case studies
   - Make.com community forum discussions
   - Stack Overflow questions
   - Any product that successfully solved this exact problem

### C. Alternative Architectures

8. **Can Make.com accept an externally-obtained OAuth token?** If our backend does the Google OAuth and gets a user's access token, can we pass it to Make.com in a webhook payload and have Make.com use it for Google API calls? Specifically:
   - Can the "Make an API Call" module in google-sheets or google-email accept a bearer token instead of a connection?
   - Can the HTTP module call Google APIs directly with a bearer token we provide?
   - Are there any Make.com modules that accept dynamic credentials?

9. **Google service account approach:**
   - Can a Google service account read ANY Google Sheet that's been shared with it? (We believe yes)
   - Can a service account create Gmail drafts in a user's mailbox? (Requires domain-wide delegation?)
   - What about service accounts + impersonation for Google Workspace users?
   - Would this only work for Google Workspace users, not personal Gmail?

10. **Hybrid approach:**
    - Our backend does Google OAuth, stores refresh tokens
    - Our backend reads the sheet and creates drafts directly using google-api-python-client
    - Make.com is removed from the Google interaction entirely
    - Make.com only handles scheduling/orchestration (or is removed entirely)
    - What are the trade-offs? The Make.com scenario logic (read sheet → filter unpaid → calculate days overdue → determine stage → create draft → update row) is ~12 modules. Is this worth keeping in Make.com or trivial to rewrite in Python?

### D. Competitive Research

11. **How do similar products handle this?** Products that read Google Sheets and/or send Gmail on behalf of users:
    - Streak CRM (Gmail-based)
    - Yet Another Mail Merge (YAMM)
    - GMass
    - Mailmeteor
    - Any "Google Sheets to email" automation tools
    - How do they handle Google OAuth? Do they have verified apps? Do they use Google Workspace Marketplace? Add-ons?

12. **Is Google Workspace Marketplace the right path?** If we published SIW as a Google Workspace Marketplace app:
    - Does that bypass the OAuth verification problem?
    - What's the review/approval process?
    - Does it limit us to Workspace users (no personal Gmail)?
    - How long does Marketplace review take?

---

## Tech Stack Context (For Understanding Constraints)

- **Backend:** Python + FastAPI, deployed on Vercel (serverless)
- **Auth:** Auth0 (email/password + magic link)
- **Database:** PostgreSQL (Neon) — users table has `sheet_id`, `make_scenario_id` fields
- **Automation:** Make.com Pro plan ($16/mo), 10,000 ops/month
- **Frontend:** Static HTML + Alpine.js + Tailwind CSS
- **Domain:** smartinvoiceworkflow.com (live)
- **Company:** Synth Insight Labs (admin@synthinsightlabs.com)

---

## Decision Criteria

The solution must:
1. **Not require users to create accounts on third-party platforms** (no Make.com signup)
2. **Not require users to manually share sheets** with a service account email
3. **Work for personal Gmail users**, not just Google Workspace
4. **Be implementable in days, not weeks** (or have a clear timeline if longer)
5. **Not scare away non-technical small business owners** (minimal scary warnings)
6. **Be maintainable** — don't create a house of cards

Nice to have:
- Keep Make.com in the stack (scenarios are already built and working)
- Minimal code changes to existing backend
- No ongoing manual approval processes

---

## Deliverable

A recommendation with:
1. **Recommended approach** with clear justification
2. **Step-by-step implementation plan**
3. **Timeline estimate**
4. **Risks and mitigations**
5. **What we'd need to change** in the current codebase and Make.com setup
6. **Links to relevant documentation** for every claim made

Do NOT recommend something without verifying it works. The reason we're in this mess is that assumptions were made without testing. If you're unsure about something, say so explicitly.
