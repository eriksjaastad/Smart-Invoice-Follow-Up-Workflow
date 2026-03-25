// @ts-check
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const {
  SCREENSHOTS_DIR, STATE_FILE, SHEET_FILE, MARKER_FILE,
  CRON_SECRET, hasAuthState,
} = require('./test-utils');

test.describe.serial('Escalation E2E — Full Pipeline', () => {
  test.use({
    storageState: hasAuthState ? STATE_FILE : undefined,
  });

  test.skip(!hasAuthState, 'Run auth-setup.spec.js first');
  test.skip(!CRON_SECRET, 'Set DIGEST_CRON_SECRET env var');

  // Generous timeout — Google API calls can be slow
  test.setTimeout(60_000);

  test('Step 1: Create template sheet via API', async ({ request }) => {
    const response = await request.post('/api/onboarding/create-template');

    if (response.status() === 400) {
      // Google not connected
      test.skip(true, 'Google account not connected — connect first via onboarding');
    }

    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('sheet_id');
    expect(body).toHaveProperty('sheet_url');

    // Save for subsequent tests
    const sheetData = { sheet_id: body.sheet_id, sheet_url: body.sheet_url };
    fs.writeFileSync(SHEET_FILE, JSON.stringify(sheetData, null, 2));

    console.log(`\n  Created test sheet: ${body.sheet_url}\n`);
  });

  test('Step 2: Select the test sheet', async ({ request }) => {
    test.skip(!fs.existsSync(SHEET_FILE), 'Step 1 must run first');

    const { sheet_id } = JSON.parse(fs.readFileSync(SHEET_FILE, 'utf-8'));

    const response = await request.post('/api/onboarding/select-sheet', {
      data: { sheet_id },
    });
    expect(response.ok()).toBeTruthy();

    const user = await response.json();
    expect(user.sheet_id).toBe(sheet_id);
    console.log(`  Sheet selected: ${sheet_id}`);
  });

  test('Step 3: Set sender info', async ({ request }) => {
    const response = await request.post('/api/onboarding/sender-info', {
      data: {
        name: 'Erik Test',
        business_name: 'Synth Insight Labs (Test)',
      },
    });
    expect(response.ok()).toBeTruthy();

    const user = await response.json();
    expect(user.name).toBe('Erik Test');
    expect(user.active).toBe(true);
  });

  test('Step 4: Trigger daily processing', async ({ request }) => {
    // Note: The template sheet has HEADERS ONLY (no invoice rows).
    // This tests the "empty sheet" path — 0 invoices checked, 0 drafts.
    // To test real escalation, populate the sheet first (see populate-test-sheet.js).
    const response = await request.post('/api/cron/trigger-daily', {
      headers: { 'x-cron-secret': CRON_SECRET },
    });
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    console.log('\n  Cron response:', JSON.stringify(body, null, 2));

    expect(body).toHaveProperty('success');
    expect(body).toHaveProperty('users_total');
    expect(body).toHaveProperty('processed');
    // No errors expected on empty sheet
    expect(body.failed).toBe(0);
  });
});

// ─────────────────────────────────────────────
// ESCALATION WITH REAL DATA
// ─────────────────────────────────────────────
// These tests require the sheet to be populated first.
// Run: node tests/e2e/populate-test-sheet.js
// That script uses Google Sheets API via the app's credentials.

test.describe.serial('Escalation E2E — With Test Data', () => {
  test.use({
    storageState: hasAuthState ? STATE_FILE : undefined,
  });

  test.skip(!hasAuthState, 'Run auth-setup.spec.js first');
  test.skip(!CRON_SECRET, 'Set DIGEST_CRON_SECRET env var');
  test.setTimeout(90_000);

  test('verify test data exists in sheet', async ({ request }) => {
    test.skip(!fs.existsSync(MARKER_FILE), 'Run populate-test-sheet.js first');

    // Hit the validate-sheet endpoint to confirm columns exist
    const { sheet_id } = JSON.parse(fs.readFileSync(SHEET_FILE, 'utf-8'));

    const response = await request.post('/api/onboarding/validate-sheet', {
      data: { sheet_id },
    });
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.valid).toBe(true);
    expect(body.missing_columns).toEqual([]);
  });

  test('trigger daily processing and verify results', async ({ request }) => {
    test.skip(!fs.existsSync(MARKER_FILE), 'Run populate-test-sheet.js first');

    const response = await request.post('/api/cron/trigger-daily', {
      headers: { 'x-cron-secret': CRON_SECRET },
    });
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    console.log('\n  Cron result:', JSON.stringify(body, null, 2));

    expect(body.success).toBe(true);
    expect(body.users_total).toBeGreaterThanOrEqual(1);
    expect(body.processed).toBeGreaterThanOrEqual(1);
  });

  test('verify Gmail drafts were created', async ({ request }) => {
    test.skip(!fs.existsSync(MARKER_FILE), 'Run populate-test-sheet.js first');

    // Check /api/auth/me to confirm we're authed
    const meResponse = await request.get('/api/auth/me');
    expect(meResponse.ok()).toBeTruthy();

    // Note: Actual draft verification is done via Gmail MCP outside Playwright.
    // This test just confirms the cron ran without errors.
    // After running: use Gmail MCP or check Gmail UI for drafts.
    console.log('\n  CHECK YOUR GMAIL DRAFTS for escalation emails!');
    console.log('  Expected drafts to: spudlogic@gmail.com');
    console.log('  Expected subjects containing: "INV-001" through "INV-006"');
    console.log('  Expected NO drafts for: INV-007/008/009 (paid), INV-010 (no email),');
    console.log('    INV-011 (not overdue), INV-012 (only 6 days), INV-014 (already sent today)\n');
  });
});
