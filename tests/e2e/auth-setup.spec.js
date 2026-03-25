/**
 * Auth Setup Script — Run once to capture authenticated browser state.
 *
 * Usage:
 *   npx playwright test tests/e2e/auth-setup.spec.js --headed
 *
 * What it does:
 *   1. Opens a real browser (headed) to the login page
 *   2. Pauses so you can manually log in via Auth0 + optionally connect Google
 *   3. After you resume, saves the browser cookies/storage to .auth/state.json
 *   4. Future tests load that file to skip the login flow entirely
 *
 * The saved state lasts until:
 *   - The session cookie expires (7 days per SessionMiddleware config)
 *   - You log out
 *   - The server secret key changes
 *
 * Re-run this script when the session expires.
 */
const { test: setup } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

// Manual login needs way more than 30s
setup.setTimeout(300_000); // 5 minutes

const AUTH_DIR = path.join(__dirname, '.auth');
const STATE_FILE = path.join(AUTH_DIR, 'state.json');

setup('authenticate via Auth0 (manual)', async ({ page }) => {
  // Ensure .auth directory exists
  if (!fs.existsSync(AUTH_DIR)) {
    fs.mkdirSync(AUTH_DIR, { recursive: true });
  }

  // Navigate to login — this will redirect to Auth0
  await page.goto('/login.html');

  // ─── MANUAL STEP ───────────────────────────────────────────────
  // The browser will open. You need to:
  //   1. Log in via Auth0 (Google social login or email/password)
  //   2. If this is your first time, complete any consent screens
  //   3. Wait until you land on /dashboard.html
  //   4. (Optional) Navigate to /onboarding.html and connect Google
  //   5. Come back to the terminal and press Enter to resume
  // ────────────────────────────────────────────────────────────────

  console.log('\n' + '═'.repeat(60));
  console.log('  MANUAL LOGIN REQUIRED');
  console.log('═'.repeat(60));
  console.log('');
  console.log('  A browser window has opened. Please:');
  console.log('');
  console.log('  1. Log in via Auth0 in the browser');
  console.log('  2. Wait until you reach the Dashboard');
  console.log('  3. (Optional) Go to /onboarding.html and connect Google');
  console.log('  4. Come back here and run: playwright.resume()');
  console.log('     in the Playwright Inspector, or press the green');
  console.log('     play button in the Inspector window');
  console.log('');
  console.log('═'.repeat(60) + '\n');

  // Pause — opens Playwright Inspector. Click "Resume" when done.
  await page.pause();

  // Verify we're actually authenticated
  const response = await page.request.get('/api/auth/me');
  if (!response.ok()) {
    throw new Error(
      `Auth check failed (${response.status()}). ` +
      'Make sure you completed login before resuming.'
    );
  }

  const user = await response.json();
  console.log(`\n  Authenticated as: ${user.email} (${user.name})`);
  console.log(`  Plan: ${user.plan}`);
  console.log(`  Google connected: ${user.google_connected ? 'yes' : 'no'}`);

  // Save the browser state (cookies, localStorage, sessionStorage)
  await page.context().storageState({ path: STATE_FILE });
  console.log(`\n  Session saved to: ${STATE_FILE}`);
  console.log('  Tests can now run without manual login.\n');
});
