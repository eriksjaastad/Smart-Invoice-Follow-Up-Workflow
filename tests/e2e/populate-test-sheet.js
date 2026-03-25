#!/usr/bin/env node
/**
 * Populate the test sheet with edge-case invoice data.
 *
 * Usage:
 *   node tests/e2e/populate-test-sheet.js
 *
 * Prerequisites:
 *   1. Run auth-setup.spec.js to capture session
 *   2. Run test_escalation_e2e.spec.js Step 1-3 to create & select the sheet
 *
 * This script uses the Google Sheets API via the app's backend session
 * to write test rows. Since there's no "write rows" API endpoint, it
 * uses the Google Sheets REST API directly via the user's access token.
 *
 * If that's not available, it falls back to prompting you to paste data manually.
 */
const fs = require('fs');
const path = require('path');

const STATE_FILE = path.join(__dirname, '.auth', 'state.json');
const SHEET_FILE = path.join(__dirname, '.auth', 'test-sheet.json');
const MARKER_FILE = path.join(__dirname, '.auth', 'test-data-populated.json');

const BASE_URL = process.env.PREVIEW_URL || 'https://smartinvoiceworkflow.com';

// Today's date for calculating overdue periods
const today = new Date();
function daysAgo(n) {
  const d = new Date(today);
  d.setDate(d.getDate() - n);
  return d.toISOString().split('T')[0]; // YYYY-MM-DD
}
function daysFromNow(n) {
  const d = new Date(today);
  d.setDate(d.getDate() + n);
  return d.toISOString().split('T')[0];
}

// Test data — each row is designed to stress a specific code path
const TEST_ROWS = [
  // [Invoice_Number, Client_Name, Client_Email, Amount, Due_Date, Sent_Date, Paid, Last_Stage_Sent, Last_Sent_At]

  // === SHOULD CREATE DRAFTS ===
  ['INV-001', 'Stage 1 Client', 'spudlogic@gmail.com', '$1,500.00', daysAgo(7), daysAgo(14), '', '', ''],
  ['INV-002', 'Stage 2 Client', 'spudlogic@gmail.com', '2500', daysAgo(14), daysAgo(21), '', '', ''],
  ['INV-003', 'Stage 3 Client', 'spudlogic@gmail.com', '$4,200.50', daysAgo(21), daysAgo(28), '', '', ''],
  ['INV-004', 'Stage 4 US Date', 'spudlogic@gmail.com', '750.00', formatUSDate(daysAgo(28)), formatUSDate(daysAgo(35)), '', '', ''],
  ['INV-005', 'Stage 5 Long Date', 'spudlogic@gmail.com', '$12,000', formatLongDate(daysAgo(35)), formatLongDate(daysAgo(42)), '', '', ''],
  ['INV-006', 'Stage 6 Final Notice', 'spudlogic@gmail.com', '888.88', daysAgo(45), daysAgo(52), '', '', ''],
  ['INV-015', 'Stage Upgrade', 'spudlogic@gmail.com', '600', daysAgo(14), daysAgo(21), '', '7', daysAgo(1)],
  ['INV-016', 'Weird Amount', 'spudlogic@gmail.com', '  $ 3,456.78  ', daysAgo(14), daysAgo(21), '', '', ''],
  ['INV-019', 'Bounce Test', 'bounce-test@invalid-domain-xyz123.com', '$750', daysAgo(14), daysAgo(21), '', '', ''],

  // === SHOULD NOT CREATE DRAFTS ===
  ['INV-007', 'Paid TRUE', 'shouldnot@getdraft.com', '$3,000', daysAgo(14), daysAgo(21), 'TRUE', '', ''],
  ['INV-008', 'Paid Yes', 'shouldnot@getdraft.com', '500', daysAgo(14), daysAgo(21), 'Yes', '', ''],
  ['INV-009', 'Paid 1', 'shouldnot@getdraft.com', '200', daysAgo(14), daysAgo(21), '1', '', ''],
  ['INV-010', 'No Email Client', '', '$999.99', daysAgo(14), daysAgo(21), '', '', ''],
  ['INV-011', 'Future Due Date', 'spudlogic@gmail.com', '$400', daysFromNow(22), daysFromNow(15), '', '', ''],
  ['INV-012', 'Only 6 Days Overdue', 'spudlogic@gmail.com', '100', daysAgo(6), daysAgo(13), '', '', ''],
  ['INV-014', 'Already Sent Today', 'spudlogic@gmail.com', '600', daysAgo(7), daysAgo(14), '', '7', today.toISOString().split('T')[0]],
  ['INV-017', 'Bad Date', 'spudlogic@gmail.com', '500', 'not-a-date', daysAgo(7), '', '', ''],
  // Blank row
  ['', '', '', '', '', '', '', '', ''],
];

function formatUSDate(isoDate) {
  const [y, m, d] = isoDate.split('-');
  return `${m}/${d}/${y}`;
}

function formatLongDate(isoDate) {
  const date = new Date(isoDate + 'T12:00:00');
  return date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
}

async function main() {
  // Check prerequisites
  if (!fs.existsSync(STATE_FILE)) {
    console.error('ERROR: No auth state. Run: npx playwright test tests/e2e/auth-setup.spec.js --headed');
    process.exit(1);
  }
  if (!fs.existsSync(SHEET_FILE)) {
    console.error('ERROR: No test sheet. Run escalation E2E Steps 1-3 first.');
    process.exit(1);
  }

  const { sheet_id } = JSON.parse(fs.readFileSync(SHEET_FILE, 'utf-8'));
  const state = JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8'));
  const cookies = state.cookies.map(c => `${c.name}=${c.value}`).join('; ');

  console.log(`\nTest sheet: ${sheet_id}`);
  console.log(`Rows to write: ${TEST_ROWS.length}`);
  console.log(`Target: ${BASE_URL}\n`);

  // Strategy: Use Google Sheets API directly via the picker-config endpoint
  // to get an access token, then write rows with the Sheets API.
  console.log('Getting Google access token via picker-config...');
  const pickerResp = await fetch(`${BASE_URL}/api/auth/google/picker-config`, {
    headers: { Cookie: cookies },
  });

  if (!pickerResp.ok) {
    console.log(`  picker-config returned ${pickerResp.status}`);
    console.log('  Falling back to manual population.\n');
    printManualInstructions(sheet_id);
    return;
  }

  const { access_token } = await pickerResp.json();
  console.log('  Got access token.\n');

  // Write rows via Google Sheets API
  console.log('Writing test data to sheet...');
  const sheetsUrl = `https://sheets.googleapis.com/v4/spreadsheets/${sheet_id}/values/A2:I${TEST_ROWS.length + 1}?valueInputOption=USER_ENTERED`;

  const writeResp = await fetch(sheetsUrl, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${access_token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      range: `A2:I${TEST_ROWS.length + 1}`,
      majorDimension: 'ROWS',
      values: TEST_ROWS,
    }),
  });

  if (!writeResp.ok) {
    const err = await writeResp.text();
    console.error(`  Write failed (${writeResp.status}): ${err}`);
    console.log('\n  Falling back to manual population.\n');
    printManualInstructions(sheet_id);
    return;
  }

  const writeResult = await writeResp.json();
  console.log(`  Wrote ${writeResult.updatedRows} rows to sheet.`);

  // Save marker file
  fs.writeFileSync(MARKER_FILE, JSON.stringify({
    sheet_id,
    populated_at: new Date().toISOString(),
    row_count: TEST_ROWS.length,
    expected_drafts: 9, // INV-001 through INV-006, INV-015, INV-016, INV-019
    expected_skips: 9,  // paid (3), no email (1), future (1), <7 days (1), already sent (1), bad date (1), blank (1)
  }, null, 2));

  console.log('\n  Test data populated successfully!');
  console.log('  Now run: npx playwright test tests/e2e/test_escalation_e2e.spec.js\n');

  // Print expected results
  console.log('  EXPECTED RESULTS:');
  console.log('  ─────────────────────────────────────────');
  console.log('  SHOULD CREATE DRAFT (9):');
  console.log('    INV-001 → Stage 1 (7 days)  → spudlogic@gmail.com');
  console.log('    INV-002 → Stage 2 (14 days) → spudlogic@gmail.com');
  console.log('    INV-003 → Stage 3 (21 days) → spudlogic@gmail.com');
  console.log('    INV-004 → Stage 4 (28 days) → spudlogic@gmail.com  [US date format]');
  console.log('    INV-005 → Stage 5 (35 days) → spudlogic@gmail.com  [long date format]');
  console.log('    INV-006 → Stage 6 (42+ days) → spudlogic@gmail.com');
  console.log('    INV-015 → Stage 2 upgrade   → spudlogic@gmail.com  [was stage 1]');
  console.log('    INV-016 → Stage 2            → spudlogic@gmail.com  [weird amount format]');
  console.log('    INV-019 → Stage 2            → bounce-test@...      [will bounce on send]');
  console.log('');
  console.log('  SHOULD SKIP (9):');
  console.log('    INV-007 → Paid=TRUE');
  console.log('    INV-008 → Paid=Yes');
  console.log('    INV-009 → Paid=1');
  console.log('    INV-010 → No email');
  console.log('    INV-011 → Not yet overdue');
  console.log('    INV-012 → Only 6 days (below stage 1)');
  console.log('    INV-014 → Already sent today (dedup)');
  console.log('    INV-017 → Invalid date format');
  console.log('    Row 19  → Blank row');
  console.log('  ─────────────────────────────────────────\n');
}

function printManualInstructions(sheetId) {
  console.log('  ═══════════════════════════════════════════════');
  console.log('  MANUAL STEP: Paste test data into the sheet');
  console.log('  ═══════════════════════════════════════════════');
  console.log(`  Open: https://docs.google.com/spreadsheets/d/${sheetId}/edit`);
  console.log('  The headers are already in row 1.');
  console.log('  Paste the following data starting in cell A2:');
  console.log('');
  TEST_ROWS.forEach(row => console.log('  ' + row.join('\t')));
  console.log('');
  console.log('  Then create the marker file:');
  console.log(`  echo '{}' > ${MARKER_FILE}`);
  console.log('  ═══════════════════════════════════════════════\n');
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
