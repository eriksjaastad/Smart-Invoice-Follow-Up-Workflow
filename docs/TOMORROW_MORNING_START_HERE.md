# 🚀 Tomorrow Morning: E2E Testing Quick Start

**Goal:** Get agent-driven E2E testing working in ~45 minutes

---

## 📋 Task Overview

You have 3 sequential tasks ready to go:

1. **#5104** - Configure Preview environment (5 min)
2. **#5105** - Update Playwright config (20 min)  
3. **#5106** - Run full test suite (15-30 min)

**When complete:** Task #4778 (E2E testing) will be DONE ✅

---

## ⚡ Quick Start Commands

### Step 1: Configure Preview Environment (Task #5104)

```bash
# Add DEBUG_MOCK_AUTH for Preview
vercel env add DEBUG_MOCK_AUTH preview
# Enter: true

# Verify
vercel env ls | grep DEBUG_MOCK_AUTH
```

**Expected:** Shows DEBUG_MOCK_AUTH for both Production (false) and Preview (true)

**Then:** `pt tasks done 5104`

---

### Step 2: Update Playwright Config (Task #5105)

**Files to edit:**
- `playwright.config.js` - Add BASE_URL logic
- `package.json` - Add test:preview script

**See:** `docs/task_5105_prompt.md` for exact code changes

**Verify:**
```bash
# Should use production URL
npm run test:prod

# Should accept PREVIEW_URL
PREVIEW_URL=https://example.com npm run test:preview
```

**Then:** `pt tasks done 5105`

---

### Step 3: Deploy and Test (Task #5106)

```bash
# Deploy to Preview
vercel deploy
# Copy the URL from output

# Set environment variable
export PREVIEW_URL="https://smart-invoice-workflow-abc123.vercel.app"

# Run all tests
npm run test:preview
```

**Expected:** All 16 tests pass ✅

**Then:** `pt tasks done 5106`

---

## 🎯 Success Criteria

### You'll know it's working when:
- ✅ Preview deployment has DEBUG_MOCK_AUTH=true
- ✅ Production still has DEBUG_MOCK_AUTH=false (security maintained)
- ✅ `npm run test:preview` runs all 16 tests
- ✅ All tests pass (signup → onboarding → payment → digest)
- ✅ Screenshots captured in tests/e2e/screenshots/

### Then you can:
- ✅ Mark Task #4778 as DONE
- ✅ Mark Task #5103 as DONE
- ✅ Commit all changes
- ✅ Deploy to production with confidence

---

## 📚 Documentation

**Detailed guides:**
- `docs/E2E_TESTING_PLAN.md` - Full strategy and rationale
- `docs/task_5104_prompt.md` - Step 1 details
- `docs/task_5105_prompt.md` - Step 2 details
- `docs/task_5106_prompt.md` - Step 3 details

**Task tracker:**
```bash
# View task tree
pt tasks tree 5103

# Show next task
pt tasks next
```

---

## 🔧 Troubleshooting

### If mock auth doesn't work in Preview:
```bash
# Check env vars
vercel env ls | grep DEBUG_MOCK_AUTH

# Should show Preview environment
# If not, repeat Task #5104
```

### If tests fail with auth errors:
```bash
# Verify Preview deployment is using correct env
vercel logs [PREVIEW_URL] | grep DEBUG_MOCK_AUTH

# Should show "true"
```

### If tests timeout:
```bash
# Check deployment status
vercel ls | head -5

# Wait for "Ready" status
```

---

## 🎬 Agent Instructions

**For an AI agent picking this up tomorrow:**

1. Read this file first
2. Run: `pt tasks show 5104` to see Task 1
3. Execute Task 1 commands
4. Mark done: `pt tasks done 5104`
5. Repeat for Tasks 5105 and 5106
6. When all pass, mark #4778 and #5103 as done

**Key insight:** Vercel Preview deployments let us enable mock auth for testing while keeping production secure. This solves the authentication problem without compromising security.

---

## ✅ Final Checklist

Before marking #4778 as DONE, verify:

- [ ] All 16 Playwright tests pass against Preview
- [ ] Screenshots captured for all steps
- [ ] Full lifecycle works: signup → onboarding → payment → digest
- [ ] Production security maintained (DEBUG_MOCK_AUTH=false)
- [ ] Agent can independently run tests using documented workflow
- [ ] Code committed to repo

---

## 📊 Current Status (End of Day 2026-03-11)

**Completed:**
- ✅ Visual snapshot infrastructure
- ✅ 16 comprehensive tests written
- ✅ 5 public route tests passing in production
- ✅ Task breakdown and documentation

**Tomorrow:**
- 🔄 Configure Preview environment
- 🔄 Update test configuration
- 🔄 Verify full E2E lifecycle
- 🔄 Close out #4778 and #5103

**Confidence level:** HIGH - Clear path forward, well-documented, tested approach.

---

**Estimated time to completion:** 45 minutes
**Risk level:** LOW - Using Vercel's built-in Preview feature, no custom infrastructure needed

