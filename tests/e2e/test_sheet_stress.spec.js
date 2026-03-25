// @ts-check
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const {
  STATE_FILE, SHEET_FILE, TEST_EMAIL,
  CRON_SECRET, hasAuthState, hasSheet, daysAgo,
} = require('./test-utils');

// Helper: get Google access token + sheet ID via Playwright request context
async function getTestContext(request) {
  const { sheet_id } = JSON.parse(fs.readFileSync(SHEET_FILE, 'utf-8'));

  // Get access token via picker-config (uses Playwright's stored cookies)
  const resp = await request.get('/api/auth/google/picker-config');
  if (!resp.ok()) throw new Error(`picker-config failed: ${resp.status()}`);
  const { access_token } = await resp.json();

  return { accessToken: access_token, sheetId: sheet_id };
}

// Helper: write rows to the test sheet (overwrites from A1)
async function writeSheet(accessToken, sheetId, headers, rows) {
  const allRows = [headers, ...rows];
  // Works for up to 26 columns (A-Z)
  const range = `A1:${String.fromCharCode(64 + headers.length)}${allRows.length}`;

  const url = `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}/values/${range}?valueInputOption=USER_ENTERED`;
  const resp = await fetch(url, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ range, majorDimension: 'ROWS', values: allRows }),
  });
  if (!resp.ok) {
    const err = await resp.text();
    throw new Error(`Sheet write failed (${resp.status}): ${err}`);
  }
  return resp.json();
}

// Helper: read sheet
async function readSheet(accessToken, sheetId, range = 'A1:Z100') {
  const resp = await fetch(
    `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}/values/${range}`,
    { headers: { Authorization: `Bearer ${accessToken}` } }
  );
  return resp.json();
}

// Standard headers
const HEADERS = ['Invoice_Number', 'Client_Name', 'Client_Email', 'Amount', 'Due_Date', 'Sent_Date', 'Paid', 'Last_Stage_Sent', 'Last_Sent_At'];

// ─────────────────────────────────────────────
// PRECONDITION CHECKS
// ─────────────────────────────────────────────

test.describe.serial('Sheet Stress Tests', () => {
  test.use({ storageState: hasAuthState ? STATE_FILE : undefined });
  test.skip(!hasAuthState, 'Run auth-setup.spec.js first');
  test.skip(!hasSheet, 'Run escalation E2E first to create test sheet');
  test.skip(!CRON_SECRET, 'Set DIGEST_CRON_SECRET env var');
  test.setTimeout(90_000);

  // ─────────────────────────────────────────────
  // #5277 — HTML INJECTION in Client_Name
  // ─────────────────────────────────────────────

  test('#5277 HTML injection in Client_Name', async ({ request }) => {
    const ctx = await getTestContext(request);

    await writeSheet(ctx.accessToken, ctx.sheetId, HEADERS, [
      ['INV-XSS', '<img src=x onerror=alert(1)>', TEST_EMAIL, '500', daysAgo(14), daysAgo(21), '', '', ''],
    ]);

    const resp = await request.post('/api/cron/trigger-daily', {
      headers: { 'x-cron-secret': CRON_SECRET },
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.success).toBe(true);
    expect(body.failed).toBe(0);

    // The draft was created (check sheet for update)
    const sheet = await readSheet(ctx.accessToken, ctx.sheetId, 'H2:I2');
    console.log('  XSS row result:', JSON.stringify(sheet.values));
    // If Last_Stage_Sent was written, draft was created without crashing
    expect(sheet.values?.[0]?.[0]).toBeTruthy();
  });

  // ─────────────────────────────────────────────
  // #5278 — UNICODE CLIENT NAMES
  // ─────────────────────────────────────────────

  test('#5278 Unicode client names', async ({ request }) => {
    const ctx = await getTestContext(request);

    await writeSheet(ctx.accessToken, ctx.sheetId, HEADERS, [
      ['INV-UNI-1', 'José García López', TEST_EMAIL, '1500', daysAgo(7), daysAgo(14), '', '', ''],
      ['INV-UNI-2', '田中太郎', TEST_EMAIL, '2000', daysAgo(14), daysAgo(21), '', '', ''],
      ['INV-UNI-3', '🚀 Rocket Corp 🎯', TEST_EMAIL, '3000', daysAgo(21), daysAgo(28), '', '', ''],
    ]);

    const resp = await request.post('/api/cron/trigger-daily', {
      headers: { 'x-cron-secret': CRON_SECRET },
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.success).toBe(true);
    expect(body.failed).toBe(0);

    // Check all 3 got processed
    const sheet = await readSheet(ctx.accessToken, ctx.sheetId, 'H2:I4');
    const stages = sheet.values?.map(r => r[0]) || [];
    console.log('  Unicode stages:', stages);
    expect(stages.length).toBe(3);
    expect(stages.every(s => s)).toBeTruthy();
  });

  // ─────────────────────────────────────────────
  // #5279 — CURRENCY FORMAT STRESS
  // ─────────────────────────────────────────────

  test('#5279 Currency format edge cases', async ({ request }) => {
    const ctx = await getTestContext(request);

    await writeSheet(ctx.accessToken, ctx.sheetId, HEADERS, [
      ['INV-CUR-1', 'Euro Client', TEST_EMAIL, '€1,500', daysAgo(7), daysAgo(14), '', '', ''],
      ['INV-CUR-2', 'Pound Client', TEST_EMAIL, '£200', daysAgo(7), daysAgo(14), '', '', ''],
      ['INV-CUR-3', 'Yen Client', TEST_EMAIL, '¥50000', daysAgo(7), daysAgo(14), '', '', ''],
      ['INV-CUR-4', 'Negative Credit', TEST_EMAIL, '-$500', daysAgo(7), daysAgo(14), '', '', ''],
      ['INV-CUR-5', 'Zero Amount', TEST_EMAIL, '$0', daysAgo(7), daysAgo(14), '', '', ''],
      ['INV-CUR-6', 'Empty Amount', TEST_EMAIL, '', daysAgo(7), daysAgo(14), '', '', ''],
    ]);

    const resp = await request.post('/api/cron/trigger-daily', {
      headers: { 'x-cron-secret': CRON_SECRET },
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    // Should not crash on any currency format
    expect(body.success).toBe(true);
    expect(body.failed).toBe(0);
    console.log('  Currency test result:', JSON.stringify(body));
  });

  // ─────────────────────────────────────────────
  // #5280 — DUPLICATE INVOICE NUMBERS
  // ─────────────────────────────────────────────

  test('#5280 Duplicate invoice numbers', async ({ request }) => {
    const ctx = await getTestContext(request);

    await writeSheet(ctx.accessToken, ctx.sheetId, HEADERS, [
      ['INV-DUP', 'Client A', TEST_EMAIL, '1000', daysAgo(7), daysAgo(14), '', '', ''],
      ['INV-DUP', 'Client B', TEST_EMAIL, '2000', daysAgo(14), daysAgo(21), '', '', ''],
    ]);

    const resp = await request.post('/api/cron/trigger-daily', {
      headers: { 'x-cron-secret': CRON_SECRET },
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.success).toBe(true);
    expect(body.failed).toBe(0);

    // Check both rows got processed (both should get drafts — different clients)
    const sheet = await readSheet(ctx.accessToken, ctx.sheetId, 'H2:I3');
    console.log('  Duplicate rows:', JSON.stringify(sheet.values));
    // Both should have Last_Stage_Sent set
    expect(sheet.values?.length).toBe(2);
  });

  // ─────────────────────────────────────────────
  // #5281 — LONG FIELD STRESS
  // ─────────────────────────────────────────────

  test('#5281 Long field values', async ({ request }) => {
    const ctx = await getTestContext(request);

    const longName = 'A'.repeat(500);
    const longInvoice = 'INV-' + 'X'.repeat(200);

    await writeSheet(ctx.accessToken, ctx.sheetId, HEADERS, [
      [longInvoice, longName, TEST_EMAIL, '1000', daysAgo(7), daysAgo(14), '', '', ''],
    ]);

    const resp = await request.post('/api/cron/trigger-daily', {
      headers: { 'x-cron-secret': CRON_SECRET },
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.success).toBe(true);
    expect(body.failed).toBe(0);
    console.log('  Long field result:', JSON.stringify(body));
  });

  // ─────────────────────────────────────────────
  // #5286 — SHEET WITH FORMULAS
  // ─────────────────────────────────────────────

  test('#5286 Formulas in cells', async ({ request }) => {
    const ctx = await getTestContext(request);

    await writeSheet(ctx.accessToken, ctx.sheetId, HEADERS, [
      ['INV-FORMULA', 'Formula Client', TEST_EMAIL, '=1000+500', '=DATE(2026,3,10)', '=DATE(2026,3,1)', '', '', ''],
    ]);

    const resp = await request.post('/api/cron/trigger-daily', {
      headers: { 'x-cron-secret': CRON_SECRET },
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.success).toBe(true);
    expect(body.failed).toBe(0);

    const sheet = await readSheet(ctx.accessToken, ctx.sheetId, 'H2:I2');
    console.log('  Formula row result:', JSON.stringify(sheet.values));
  });

  // ─────────────────────────────────────────────
  // #5288 — COMMAS IN CLIENT NAMES
  // ─────────────────────────────────────────────

  test('#5288 Commas in client names', async ({ request }) => {
    const ctx = await getTestContext(request);

    await writeSheet(ctx.accessToken, ctx.sheetId, HEADERS, [
      ['INV-COMMA', 'Smith, Johnson & Associates, LLC', TEST_EMAIL, '5000', daysAgo(14), daysAgo(21), '', '', ''],
    ]);

    const resp = await request.post('/api/cron/trigger-daily', {
      headers: { 'x-cron-secret': CRON_SECRET },
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.success).toBe(true);
    expect(body.failed).toBe(0);

    const sheet = await readSheet(ctx.accessToken, ctx.sheetId, 'H2:I2');
    console.log('  Comma name result:', JSON.stringify(sheet.values));
    expect(sheet.values?.[0]?.[0]).toBeTruthy();
  });

  // ─────────────────────────────────────────────
  // #5289 — EMPTY / WHITESPACE-ONLY FIELDS
  // ─────────────────────────────────────────────

  test('#5289 Empty and whitespace-only fields', async ({ request }) => {
    const ctx = await getTestContext(request);

    await writeSheet(ctx.accessToken, ctx.sheetId, HEADERS, [
      ['INV-WS-1', '   ', TEST_EMAIL, '   ', daysAgo(14), daysAgo(21), '', '', ''],
      ['INV-WS-2', 'Real Client', '   ', '1000', daysAgo(14), daysAgo(21), '', '', ''],
      ['INV-WS-3', 'Real Client', TEST_EMAIL, '1000', '   ', daysAgo(21), '', '', ''],
    ]);

    const resp = await request.post('/api/cron/trigger-daily', {
      headers: { 'x-cron-secret': CRON_SECRET },
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    // Should NOT crash — some rows skipped, some processed
    expect(body.success).toBe(true);
    expect(body.failed).toBe(0);
    console.log('  Whitespace result:', JSON.stringify(body));
  });

  // ─────────────────────────────────────────────
  // #5287 — LARGE SHEET (500+ rows)
  // ─────────────────────────────────────────────

  test('#5287 Large sheet — 500 rows', async ({ request }) => {
    const ctx = await getTestContext(request);

    // Generate 500 rows
    const rows = [];
    for (let i = 1; i <= 500; i++) {
      rows.push([
        `INV-BULK-${String(i).padStart(4, '0')}`,
        `Bulk Client ${i}`,
        TEST_EMAIL,
        `${1000 + i}`,
        daysAgo(14),
        daysAgo(21),
        '',
        '',
        '',
      ]);
    }

    await writeSheet(ctx.accessToken, ctx.sheetId, HEADERS, rows);

    const start = Date.now();
    const resp = await request.post('/api/cron/trigger-daily', {
      headers: { 'x-cron-secret': CRON_SECRET },
    });
    const elapsed = Date.now() - start;

    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    console.log(`  500-row result (${elapsed}ms):`, JSON.stringify(body));

    expect(body.success).toBe(true);
    expect(body.failed).toBe(0);

    // Should complete within 60 seconds
    expect(elapsed).toBeLessThan(60_000);
  });
});
