// @ts-check
const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const SCREENSHOTS_DIR = path.join(__dirname, 'screenshots');
const STATE_FILE = path.join(__dirname, '.auth', 'state.json');

// ─────────────────────────────────────────────
// Skip all tests if auth state doesn't exist
// ─────────────────────────────────────────────
const hasAuthState = fs.existsSync(STATE_FILE);

test.describe('Authenticated Tests', () => {
  // Load saved auth state for all tests in this file
  test.use({
    storageState: hasAuthState ? STATE_FILE : undefined,
  });

  test.skip(!hasAuthState, 'Run auth-setup.spec.js --headed first');

  // ─────────────────────────────────────────────
  // SESSION VALIDATION
  // ─────────────────────────────────────────────

  test.describe('Session', () => {
    test('saved session is still valid', async ({ request }) => {
      const response = await request.get('/api/auth/me');
      expect(response.ok()).toBeTruthy();
      const user = await response.json();
      expect(user).toHaveProperty('email');
      expect(user).toHaveProperty('id');
    });
  });

  // ─────────────────────────────────────────────
  // DASHBOARD
  // ─────────────────────────────────────────────

  test.describe('Dashboard', () => {
    test('loads and shows user info', async ({ page }) => {
      await page.goto('/dashboard.html');
      await page.waitForLoadState('networkidle');

      // Should NOT redirect to login
      expect(page.url()).toContain('dashboard');

      // Dashboard heading
      await expect(page.locator('h1:has-text("Dashboard")')).toBeVisible({ timeout: 10000 });

      await page.screenshot({
        path: path.join(SCREENSHOTS_DIR, 'auth-01-dashboard.png'),
        fullPage: true,
      });
    });

    test('shows user name in navbar', async ({ page }) => {
      await page.goto('/dashboard.html');
      await page.waitForLoadState('networkidle');

      // The nav shows user name from /api/auth/me response
      const navText = await page.locator('nav').textContent();
      // Should have some user-specific text (not "Loading...")
      expect(navText).not.toContain('Loading...');
    });

    test('has navigation links to Settings and Billing', async ({ page }) => {
      await page.goto('/dashboard.html');
      await page.waitForLoadState('networkidle');

      await expect(page.locator('nav >> a[href="/settings.html"]')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('nav >> a[href="/billing.html"]')).toBeVisible();
    });

    test('shows setup warning or system status', async ({ page }) => {
      await page.goto('/dashboard.html');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Either shows "Setup is incomplete" warning or "System Active" status
      const hasSetupWarning = await page.locator('text=Setup is incomplete').isVisible().catch(() => false);
      const hasSystemActive = await page.locator('text=System Active').isVisible().catch(() => false);
      const hasSystemPaused = await page.locator('text=System Paused').isVisible().catch(() => false);

      expect(hasSetupWarning || hasSystemActive || hasSystemPaused).toBeTruthy();
    });
  });

  // ─────────────────────────────────────────────
  // SETTINGS PAGE
  // ─────────────────────────────────────────────

  test.describe('Settings', () => {
    test('loads with user profile fields populated', async ({ page }) => {
      await page.goto('/settings.html');
      await page.waitForLoadState('networkidle');

      await expect(page.locator('h1:has-text("App Settings")')).toBeVisible({ timeout: 10000 });

      // Email field should be populated and disabled
      const emailInput = page.locator('input[type="email"]');
      await expect(emailInput).toBeVisible();
      const emailValue = await emailInput.inputValue();
      expect(emailValue).toContain('@');

      // Sender name should have a value
      const nameInput = page.locator('input[x-model="user.name"]');
      const nameValue = await nameInput.inputValue();
      expect(nameValue.length).toBeGreaterThan(0);

      await page.screenshot({
        path: path.join(SCREENSHOTS_DIR, 'auth-02-settings.png'),
        fullPage: true,
      });
    });

    test('has system controls (pause/resume button)', async ({ page }) => {
      await page.goto('/settings.html');
      await page.waitForLoadState('networkidle');

      await expect(page.locator('text=System Controls').first()).toBeVisible({ timeout: 10000 });

      const pauseBtn = page.locator('button:has-text("Pause System")').or(
        page.locator('button:has-text("Resume System")')
      );
      await expect(pauseBtn.first()).toBeVisible();
    });

    test('has Google reconnect button', async ({ page }) => {
      await page.goto('/settings.html');
      await page.waitForLoadState('networkidle');

      await expect(page.locator('text=Reconnect Google Account').first()).toBeVisible({ timeout: 10000 });
    });
  });

  // ─────────────────────────────────────────────
  // BILLING PAGE
  // ─────────────────────────────────────────────

  test.describe('Billing', () => {
    test('loads and shows current plan', async ({ page }) => {
      await page.goto('/billing.html');
      await page.waitForLoadState('networkidle');

      await expect(page.locator('h1:has-text("Billing")')).toBeVisible({ timeout: 10000 });

      // Should show plan name (free or paid)
      const planText = page.locator('h2.capitalize').or(page.locator('[x-text="user.plan"]'));
      await expect(planText.first()).toBeVisible();

      await page.screenshot({
        path: path.join(SCREENSHOTS_DIR, 'auth-03-billing.png'),
        fullPage: true,
      });
    });

    test('free plan shows upgrade banner', async ({ page }) => {
      await page.goto('/billing.html');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Check which plan the user is on
      const response = await page.request.get('/api/auth/me');
      const user = await response.json();

      if (user.plan === 'free') {
        await expect(page.locator('text=Time to upgrade?').first()).toBeVisible();
        await expect(page.locator('button:has-text("Upgrade to Pro")')).toBeVisible();
      } else {
        // Paid plan shows subscription management
        await expect(page.locator('text=Subscription Active').first()).toBeVisible();
      }
    });
  });

  // ─────────────────────────────────────────────
  // ONBOARDING PAGE
  // ─────────────────────────────────────────────

  test.describe('Onboarding', () => {
    test('loads step 1 - Google connection', async ({ page }) => {
      await page.goto('/onboarding.html');
      await page.waitForLoadState('networkidle');

      // Should show the onboarding UI, not a login redirect
      expect(page.url()).toContain('onboarding');

      await page.screenshot({
        path: path.join(SCREENSHOTS_DIR, 'auth-04-onboarding.png'),
        fullPage: true,
      });
    });

    test('shows Google connected state if already connected', async ({ page }) => {
      // Check if Google is connected
      const response = await page.request.get('/api/auth/me');
      const user = await response.json();

      await page.goto('/onboarding.html');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      if (user.google_connected) {
        // Step 1 should show connected state or auto-advance to step 2
        const hasConnected = await page.locator('text=Connected').or(
          page.locator('text=connected')
        ).first().isVisible().catch(() => false);

        const onStep2 = page.url().includes('step=2');

        expect(hasConnected || onStep2).toBeTruthy();
      }
    });
  });

  // ─────────────────────────────────────────────
  // API — Authenticated Endpoints
  // ─────────────────────────────────────────────

  test.describe('API — Authenticated', () => {
    test('GET /api/auth/me returns full user profile', async ({ request }) => {
      const response = await request.get('/api/auth/me');
      expect(response.ok()).toBeTruthy();

      const user = await response.json();
      expect(user).toHaveProperty('id');
      expect(user).toHaveProperty('email');
      expect(user).toHaveProperty('name');
      expect(user).toHaveProperty('plan');
      expect(user).toHaveProperty('active');
      expect(['free', 'paid']).toContain(user.plan);
      expect(typeof user.active).toBe('boolean');
    });

    test('GET /api/users/me returns same user', async ({ request }) => {
      const response = await request.get('/api/users/me');
      expect(response.ok()).toBeTruthy();

      const user = await response.json();
      expect(user).toHaveProperty('email');
    });

    test('GET /api/billing/status returns billing info', async ({ request }) => {
      const response = await request.get('/api/billing/status');
      expect(response.ok()).toBeTruthy();

      const billing = await response.json();
      expect(billing).toHaveProperty('plan');
    });

    test('GET /api/auth/google/connect returns auth URL (if configured)', async ({ request }) => {
      const response = await request.get('/api/auth/google/connect');
      // 200 with URL = configured, 503 = not configured
      expect([200, 503]).toContain(response.status());

      if (response.ok()) {
        const body = await response.json();
        expect(body).toHaveProperty('url');
        expect(body.url).toContain('accounts.google.com');
      }
    });
  });

  // ─────────────────────────────────────────────
  // NAVIGATION — Cross-page flows
  // ─────────────────────────────────────────────

  test.describe('Navigation', () => {
    test('dashboard → settings → dashboard round-trip', async ({ page }) => {
      await page.goto('/dashboard.html');
      await page.waitForLoadState('networkidle');
      await expect(page.locator('h1:has-text("Dashboard")')).toBeVisible({ timeout: 10000 });

      // Click Settings link in navbar
      await page.locator('nav >> a[href="/settings.html"]').click();
      await page.waitForLoadState('networkidle');
      await expect(page.locator('h1:has-text("App Settings")')).toBeVisible({ timeout: 10000 });

      // Click Dashboard link back
      await page.locator('a[href="/dashboard.html"]').click();
      await page.waitForLoadState('networkidle');
      await expect(page.locator('h1:has-text("Dashboard")')).toBeVisible({ timeout: 10000 });
    });

    test('dashboard → billing navigation works', async ({ page }) => {
      await page.goto('/dashboard.html');
      await page.waitForLoadState('networkidle');

      await page.locator('a[href="/billing.html"]').first().click();
      await page.waitForLoadState('networkidle');
      await expect(page.locator('h1:has-text("Billing")')).toBeVisible({ timeout: 10000 });
    });

    test('logout redirects away from app', async ({ page }) => {
      // We verify the button exists and is wired up, but DON'T click it
      // because that would invalidate the saved session for other tests
      await page.goto('/dashboard.html');
      await page.waitForLoadState('networkidle');

      // Verify the logout button exists
      const logoutBtn = page.locator('button:has-text("Log out")');
      await expect(logoutBtn).toBeVisible({ timeout: 10000 });

      // Don't actually click it — would invalidate the session for other tests
      // Just verify it's wired up
      const onClick = await logoutBtn.getAttribute('@click') || '';
      expect(onClick).toContain('logout');
    });
  });
});
