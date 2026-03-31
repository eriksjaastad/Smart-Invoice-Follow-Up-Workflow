# E2E Testing Implementation Plan

## Current Situation (as of 2026-03-11)

### ✅ What We Have
- Visual snapshot infrastructure complete (playwright.config.js, test files)
- 5/16 tests passing (public routes only)
- Vercel CLI installed and working
- Dev, Preview, and Production environments on Vercel
- All environment variables already set for Production

### ❌ What's Blocking Us
- Task #4778 (E2E testing) is NOT DONE - blocked by authentication
- 11/16 tests fail because DEBUG_MOCK_AUTH=false in production (correct security)
- Need to test full lifecycle: signup → onboarding → payment → digest
- Task #4778 is blocked by Task #5103 (staging setup)

---

## Solution: Deploy to Preview with Mock Auth Enabled

### Key Insight
**Vercel Preview deployments are perfect for this:**
- `vercel deploy` (without `--prod`) creates a Preview deployment
- Preview deployments get their own environment variables
- We can enable DEBUG_MOCK_AUTH=true ONLY in Preview
- Production stays secure with DEBUG_MOCK_AUTH=false

### The Plan (3 Tasks)

---

## Task 1: Configure Preview Environment Variables

**Goal:** Set DEBUG_MOCK_AUTH=true for Preview environment only

**Commands:**
```bash
# Check current DEBUG_MOCK_AUTH setting
vercel env ls | grep DEBUG_MOCK_AUTH

# Add DEBUG_MOCK_AUTH=true for Preview environment
vercel env add DEBUG_MOCK_AUTH preview
# When prompted, enter: true

# Verify it's set
vercel env ls | grep DEBUG_MOCK_AUTH
```

**Expected result:**
- DEBUG_MOCK_AUTH=false in Production
- DEBUG_MOCK_AUTH=true in Preview
- All other env vars already exist (you said you add them to all three)

**Acceptance criteria:**
- [ ] DEBUG_MOCK_AUTH shows "Preview" in environments column
- [ ] Value is "true" for Preview
- [ ] Production value remains "false"

---

## Task 2: Deploy to Preview and Test

**Goal:** Create a Preview deployment and verify mock auth works

**Commands:**
```bash
# Deploy to Preview (NOT production)
vercel deploy

# This will output a URL like:
# https://smart-invoice-workflow-abc123.vercel.app
```

**Manual verification:**
1. Visit the Preview URL
2. Navigate to `/api/auth/debug-login?user_id=test@example.com`
3. Verify you get redirected to dashboard
4. Verify you can access protected routes

**Acceptance criteria:**
- [ ] Preview deployment created successfully
- [ ] Preview URL accessible
- [ ] Mock auth endpoint works (can bypass Auth0)
- [ ] Dashboard loads without real Auth0 login

---

## Task 3: Update Playwright Tests for Multi-Environment

**Goal:** Make tests run against Preview OR Production based on env var

**Files to modify:**
1. `playwright.config.js` - Add BASE_URL logic
2. `package.json` - Add test:preview script
3. Update test files if needed

**Changes:**

**playwright.config.js:**
```javascript
const BASE_URL = process.env.TEST_ENV === 'preview'
  ? process.env.PREVIEW_URL || 'https://smart-invoice-workflow-[latest].vercel.app'
  : 'https://smartinvoiceworkflow.com';

export default defineConfig({
  use: {
    baseURL: BASE_URL,
    // ... rest of config
  },
});
```

**package.json:**
```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:preview": "TEST_ENV=preview playwright test",
    "test:prod": "playwright test"
  }
}
```

**Acceptance criteria:**
- [ ] `npm run test:preview` runs against Preview URL
- [ ] `npm run test:prod` runs against Production URL
- [ ] All 16 tests pass against Preview
- [ ] Public tests (5) still pass against Production

---

## Task 4: Document Agent Testing Workflow

**Goal:** Create clear instructions for agents to run E2E tests

**File:** `docs/AGENT_E2E_TESTING.md`

**Content:**
```markdown
# Agent E2E Testing Guide

## Quick Start

1. Deploy to Preview:
   ```bash
   vercel deploy
   # Copy the URL from output
   ```

2. Set Preview URL:
   ```bash
   export PREVIEW_URL="https://smart-invoice-workflow-abc123.vercel.app"
   ```

3. Run tests:
   ```bash
   npm run test:preview
   ```

## Expected Results
- All 16 tests should pass
- Screenshots saved to tests/e2e/screenshots/
- Full lifecycle tested: signup → onboarding → payment → digest

## Troubleshooting
- If auth fails: Verify DEBUG_MOCK_AUTH=true in Preview env
- If tests timeout: Check Preview deployment is Ready
- If API errors: Check environment variables in Vercel dashboard
```

**Acceptance criteria:**
- [ ] Documentation exists
- [ ] Agent can follow instructions independently
- [ ] No manual Auth0 login required

---

## Success Criteria (Overall)

### Task #5103 Complete When:
- [ ] Preview environment configured with DEBUG_MOCK_AUTH=true
- [ ] Playwright supports multi-environment testing
- [ ] Agent documentation exists
- [ ] Verified: All 16 tests pass against Preview

### Task #4778 Complete When:
- [ ] All 6 acceptance criteria from original prompt met:
  1. Signup flow works
  2. Sheet connection works
  3. Create template works
  4. Daily processing verified
  5. Stripe payment flow tested
  6. Digest email tested
- [ ] Screenshots captured for all steps
- [ ] Tests committed to repo

---

## Timeline Estimate

**Tomorrow morning session:**
- Task 1: 5 minutes (configure env vars)
- Task 2: 10 minutes (deploy and verify)
- Task 3: 20 minutes (update test config)
- Task 4: 10 minutes (documentation)
- **Total: ~45 minutes**

Then run full test suite and verify all 16 tests pass.

---

## Risks and Mitigations

**Risk:** Preview URL changes with each deployment
**Mitigation:** Use `vercel ls` to get latest Preview URL, or use `vercel inspect` to get specific deployment URL

**Risk:** Environment variables not propagating to Preview
**Mitigation:** Use `vercel env pull .env.preview` to verify what Preview sees

**Risk:** Database conflicts between Preview and Production
**Mitigation:** Preview uses same DATABASE_URL - test users will be in production DB but isolated by email (use test-agent-TIMESTAMP@example.com pattern)

---

## Alternative: Test Auth0 Account (Backup Plan)

If Preview approach doesn't work, we can create a real test Auth0 account:

1. Create test user in Auth0: test-agent@smartinvoice.com
2. Store credentials in .env.test (gitignored)
3. Update Playwright to use real login flow
4. Tests run against Production with real auth

**Pros:** Tests production environment exactly
**Cons:** Requires managing Auth0 test users, slower tests (real OAuth flow)

