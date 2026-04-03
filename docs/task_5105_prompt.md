# Task #5105: Update Playwright Config for Multi-Environment Testing

## Context
Playwright tests currently hardcode the production URL. We need to support testing against Preview deployments (with mock auth) AND production (public routes only).

## Goal
Make Playwright tests environment-aware so agents can run full E2E tests against Preview.

## Files to Modify

### 1. playwright.config.js

**Add environment-based URL logic:**

```javascript
// At the top of the file, before defineConfig
const BASE_URL = process.env.PREVIEW_URL 
  || (process.env.TEST_ENV === 'production' 
      ? 'https://smartinvoiceworkflow.com' 
      : 'https://smartinvoiceworkflow.com'); // default to prod

export default defineConfig({
  use: {
    baseURL: BASE_URL,
    // ... rest of existing config
  },
  // ... rest of config
});
```

### 2. package.json

**Add test scripts:**

```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:preview": "playwright test",
    "test:prod": "TEST_ENV=production playwright test"
  }
}
```

### 3. Create .env.test.example

**Document environment variables for testing:**

```bash
# Preview deployment URL (get from: vercel ls)
PREVIEW_URL=https://smart-invoice-workflow-abc123.vercel.app

# Or use production
TEST_ENV=production
```

### 4. Update .gitignore

**Ensure test env files are ignored:**

```
.env.test
.env.preview
```

## Acceptance Criteria

### Configuration
- [ ] playwright.config.js reads PREVIEW_URL or TEST_ENV
- [ ] Default behavior unchanged (tests against production)
- [ ] package.json has test:preview and test:prod scripts
- [ ] .env.test.example created with documentation

### Verification
- [ ] `PREVIEW_URL=https://example.com npm run test:preview` uses example.com
- [ ] `npm run test:prod` uses smartinvoiceworkflow.com
- [ ] No hardcoded URLs remain in test files

### Testing
- [ ] Run `npm run test:prod` - public tests (5) should pass
- [ ] Set PREVIEW_URL to a Preview deployment
- [ ] Run `npm run test:preview` - should attempt to run all 16 tests

## Implementation Notes

**Getting Preview URL:**
```bash
# Deploy to preview
vercel deploy

# Or get latest preview URL
vercel ls | grep Preview | head -1
```

**Test locally:**
```bash
# Set preview URL
export PREVIEW_URL="https://smart-invoice-workflow-abc123.vercel.app"

# Run tests
npm run test:preview
```

## Time Estimate
20 minutes

## Dependencies
- Requires Task #5104 complete (Preview env vars configured)
- Blocks Task #5106 (running full test suite)

## Notes
- Don't modify test logic - only configuration
- Tests should work against any URL (preview or production)
- Agent will use this to test full lifecycle against Preview

