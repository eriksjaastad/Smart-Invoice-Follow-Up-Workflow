# Task #5104: Configure Preview Environment with DEBUG_MOCK_AUTH=true

## Context
We have Vercel environments: Production, Preview, and Development. Currently DEBUG_MOCK_AUTH is only set for Production (value: false). We need to enable it for Preview so agents can test the full E2E flow without real Auth0 credentials.

## Goal
Configure Vercel Preview environment to have DEBUG_MOCK_AUTH=true while keeping Production at false.

## Steps

### 1. Check Current Configuration
```bash
vercel env ls | grep DEBUG_MOCK_AUTH
```

**Expected:** Should show DEBUG_MOCK_AUTH only for Production environment.

### 2. Add DEBUG_MOCK_AUTH for Preview
```bash
vercel env add DEBUG_MOCK_AUTH preview
```

When prompted for value, enter: `true`

### 3. Verify Configuration
```bash
vercel env ls | grep DEBUG_MOCK_AUTH
```

**Expected output:**
```
DEBUG_MOCK_AUTH    Encrypted    Production    [date]
DEBUG_MOCK_AUTH    Encrypted    Preview       [date]
```

### 4. Optional: Add for Development Too
```bash
vercel env add DEBUG_MOCK_AUTH development
```

Enter: `true`

## Acceptance Criteria
- [ ] DEBUG_MOCK_AUTH exists for Preview environment with value "true"
- [ ] DEBUG_MOCK_AUTH exists for Production environment with value "false" (unchanged)
- [ ] `vercel env ls` shows both entries
- [ ] No other environment variables were modified

## Verification
After completing, run:
```bash
vercel env ls | grep -E "(DEBUG_MOCK_AUTH|ENVIRONMENT)" | sort
```

Should show DEBUG_MOCK_AUTH for both Production and Preview.

## Time Estimate
5 minutes

## Notes
- This does NOT require a new deployment - env vars are set for future deployments
- Next task (#5105) will deploy to Preview and verify mock auth works
- Production security is maintained (DEBUG_MOCK_AUTH=false)

