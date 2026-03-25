const path = require('path');
const fs = require('fs');

const SCREENSHOTS_DIR = path.join(__dirname, 'screenshots');
const AUTH_DIR = path.join(__dirname, '.auth');
const STATE_FILE = path.join(AUTH_DIR, 'state.json');
const SHEET_FILE = path.join(AUTH_DIR, 'test-sheet.json');
const MARKER_FILE = path.join(AUTH_DIR, 'test-data-populated.json');

const TEST_EMAIL = process.env.TEST_EMAIL || 'spudlogic@gmail.com';
const CRON_SECRET = process.env.DIGEST_CRON_SECRET || '';
const hasAuthState = fs.existsSync(STATE_FILE);
const hasSheet = fs.existsSync(SHEET_FILE);

function daysAgo(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().split('T')[0];
}

function daysFromNow(n) {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d.toISOString().split('T')[0];
}

module.exports = {
  SCREENSHOTS_DIR, AUTH_DIR, STATE_FILE, SHEET_FILE, MARKER_FILE,
  TEST_EMAIL, CRON_SECRET, hasAuthState, hasSheet,
  daysAgo, daysFromNow,
};
