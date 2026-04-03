# Task #5106: Verify All 16 E2E Tests Pass Against Preview

## Context
Tasks #5104 and #5105 set up Preview environment with mock auth and configured Playwright for multi-environment testing. Now we verify the full E2E lifecycle works.

## Goal
Deploy to Preview, run all 16 Playwright tests, and verify they pass. This proves the full user journey works: signup → onboarding → payment → digest.

## Steps

### 1. Deploy to Preview
```bash
# Deploy to preview (NOT production)
vercel deploy

# Save the URL from output
# Example: https://smart-invoice-workflow-abc123.vercel.app
```

### 2. Verify Mock Auth Works
```bash
# Test the debug login endpoint
curl "https://[PREVIEW_URL]/api/auth/debug-login?user_id=test@example.com"

# Should return redirect to dashboard
# Or visit in browser and verify you can access dashboard without Auth0
```

### 3. Set Preview URL
```bash
export PREVIEW_URL="https://smart-invoice-workflow-abc123.vercel.app"
```

### 4. Run Full Test Suite
```bash
npm run test:preview
```

### 5. Review Results
Check:
- How many tests passed (target: 16/16)
- Screenshots captured in tests/e2e/screenshots/
- Any failures and their error messages

## Acceptance Criteria

### Deployment
- [ ] Preview deployment created successfully
- [ ] Preview URL accessible
- [ ] Mock auth endpoint works (can bypass Auth0)

### Test Results
- [ ] All 16 tests pass (or document which fail and why)
- [ ] Screenshots captured for all test steps
- [ ] No authentication errors (mock auth working)

### Specific Test Coverage (from original #4778)
- [ ] **Scenario 1:** Signup flow (Auth0 → Dashboard) ✅
- [ ] **Scenario 2:** Sheet connection onboarding ✅
- [ ] **Scenario 3:** Create template ✅
- [ ] **Scenario 4:** Daily processing trigger ✅
- [ ] **Scenario 5:** Stripe payment flow ✅
- [ ] **Scenario 6:** Digest email ✅

### Documentation
- [ ] Test results documented (pass/fail counts)
- [ ] Any failures have clear error messages
- [ ] Screenshots committed to repo

## Troubleshooting

### If tests fail with auth errors:
```bash
# Check Preview env vars
vercel env ls | grep DEBUG_MOCK_AUTH

# Should show Preview environment with value
# If not, go back to Task #5104
```

### If tests timeout:
```bash
# Check deployment status
vercel ls | head -5

# Should show "Ready" status
# If "Building", wait for deployment to complete
```

### If API errors (500, 503):
```bash
# Check Preview logs
vercel logs [PREVIEW_URL]

# Look for missing environment variables
# Verify all env vars exist for Preview:
vercel env ls | grep Preview
```

## Expected Outcome

**Success looks like:**
```
Running 16 tests using 1 worker

✓ [chromium] › test_visual_snapshots.spec.js:10:5 › Landing page (1s)
✓ [chromium] › test_visual_snapshots.spec.js:15:5 › Pricing page (1s)
✓ [chromium] › test_visual_snapshots.spec.js:20:5 › Login page (1s)
✓ [chromium] › test_visual_snapshots.spec.js:25:5 › Auth0 redirect (2s)
✓ [chromium] › test_visual_snapshots.spec.js:30:5 › Dashboard (mock auth) (2s)
✓ [chromium] › test_visual_snapshots.spec.js:40:5 › Onboarding step 1 (2s)
✓ [chromium] › test_visual_snapshots.spec.js:50:5 › Onboarding step 2 (2s)
... (all 16 tests)

16 passed (30s)
```

## Time Estimate
15-30 minutes (including debugging if needed)

## Dependencies
- Requires Task #5104 complete (env vars)
- Requires Task #5105 complete (Playwright config)

## Success Criteria for Task #4778
When this task passes, Task #4778 (E2E testing) can be marked DONE because:
- All 6 acceptance criteria met
- Full lifecycle tested
- Screenshots captured
- Infrastructure proven to work

## Notes
- This is the final verification step
- If all tests pass, we can commit everything and close #4778
- If some tests fail, document which ones and create follow-up tasks
- Agent can now independently test the full pipeline using this workflow

