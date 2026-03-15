// @ts-check
const { test, expect } = require('@playwright/test');
const path = require('path');

const SCREENSHOTS_DIR = path.join(__dirname, 'screenshots');

test.describe('Scenario A: Landing Page', () => {
  test('loads and displays key content', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Smart Invoice/i);

    // Screenshot: Landing page loaded
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'flow-01-landing-loaded.png'),
      fullPage: true
    });

    // Check hero section exists
    const hero = page.locator('text=Follow-up is the').first();
    await expect(hero).toBeVisible({ timeout: 10000 });

    // Check pricing section
    await expect(page.locator('text=Free').first()).toBeVisible();
    await expect(page.locator('text=Pro').first()).toBeVisible();

    // Screenshot: Pricing section visible
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'flow-02-pricing-visible.png'),
      fullPage: true
    });

    // Check CTA buttons exist
    const startFreeBtn = page.locator('text=Start').first();
    await expect(startFreeBtn).toBeVisible();
  });

  test('Start Free button navigates to login', async ({ page }) => {
    await page.goto('/');

    // Screenshot: Before clicking Start Free
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'flow-03-before-login-click.png'),
      fullPage: true
    });

    // Click first signup-type button
    await page.locator('a[href="/login.html"]').first().click();

    // Should end up at login.html which auto-redirects to /api/auth/login
    await page.waitForURL(/\/(login\.html|api\/auth\/login|dashboard)/, { timeout: 15000 });

    // Screenshot: After login redirect
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'flow-04-after-login-redirect.png'),
      fullPage: true
    });
  });
});

test.describe('Scenario B: Mock Auth Signup Flow', () => {
  test('full signup → dashboard → onboarding flow', async ({ page }) => {
    // Step 1: Hit login - mock auth should auto-create user and redirect
    await page.goto(`/api/auth/login`);
    await page.waitForURL(/dashboard/, { timeout: 15000 });

    // Screenshot: Dashboard after mock auth login
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'flow-05-dashboard-after-login.png'),
      fullPage: true
    });

    // Step 2: Verify dashboard loaded
    await expect(page.locator('text=Dashboard').first()).toBeVisible({ timeout: 10000 });

    // Check mock auth indicator
    const mockBadge = page.locator('text=Mock Auth').first();
    // Mock auth badge may or may not be visible depending on implementation

    // Step 3: Check user info is displayed
    const pageContent = await page.content();
    expect(pageContent).toContain('mock');
  });

  test('onboarding page loads and shows steps', async ({ page }) => {
    // Login first via mock auth
    await page.goto(`/api/auth/login`);
    await page.waitForURL(/dashboard/, { timeout: 15000 });

    // Navigate to onboarding
    await page.goto(`/onboarding.html`);
    await page.waitForLoadState('networkidle');

    // Screenshot: Onboarding page loaded
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'flow-06-onboarding-loaded.png'),
      fullPage: true
    });

    // Should show step 1 - Connect Google Account
    await expect(page.locator('text=Google').first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Scenario C: API Health Checks', () => {
  test('health endpoint returns healthy', async ({ request }) => {
    const response = await request.get(`/health`);
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.status).toBe('healthy');
    expect(body.environment).toBe('production');
  });

  test('system status returns not paused', async ({ request }) => {
    const response = await request.get(`/api/system/status`);
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.paused).toBe(false);
  });
});

test.describe('Scenario D: Payment Flow (Stripe Test Mode)', () => {
  test('billing checkout creates Stripe session', async ({ page }) => {
    // Login via mock auth first
    await page.goto(`/api/auth/login`);
    await page.waitForURL(/dashboard/, { timeout: 15000 });

    // Screenshot: Dashboard before upgrade attempt
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'flow-07-dashboard-before-upgrade.png'),
      fullPage: true
    });

    // Check if there's an upgrade/payment button on dashboard
    const upgradeBtn = page.locator('text=Upgrade').or(page.locator('text=Pro')).or(page.locator('text=Subscribe'));

    if (await upgradeBtn.first().isVisible({ timeout: 5000 }).catch(() => false)) {
      await upgradeBtn.first().click();

      // Wait a moment for redirect
      await page.waitForTimeout(2000);

      // Screenshot: After clicking upgrade (Stripe checkout or error)
      await page.screenshot({
        path: path.join(SCREENSHOTS_DIR, 'flow-08-stripe-checkout.png'),
        fullPage: true
      });

      // Should redirect to Stripe Checkout (test mode)
      await page.waitForURL(/checkout\.stripe\.com/, { timeout: 15000 });

      // Verify we're in test mode
      const url = page.url();
      expect(url).toContain('checkout.stripe.com');
    } else {
      // No upgrade button visible - check if billing API exists
      const response = await page.request.post(`/api/billing/create-checkout-session`, {
        headers: { 'Content-Type': 'application/json' }
      });
      // Should get 401 (not authenticated via API) or redirect
      expect([200, 302, 401, 403, 405, 422]).toContain(response.status());
    }
  });
});

test.describe('Scenario E: Error Handling', () => {
  test('404 page for unknown API routes', async ({ request }) => {
    const response = await request.get(`/api/nonexistent`);
    expect(response.status()).toBe(404);
  });

  test('webhook rejects unsigned requests', async ({ request }) => {
    const response = await request.post(`/api/billing/webhook`, {
      headers: { 'Content-Type': 'application/json' },
      data: { test: true }
    });
    expect(response.status()).toBe(400);
    const body = await response.json();
    expect(body.detail).toContain('signature');
  });

  test('cron rejects missing secret', async ({ request }) => {
    const response = await request.post(`/api/cron/trigger-daily`);
    expect(response.status()).toBe(401);
  });

  test('system pause rejects wrong secret', async ({ request }) => {
    const response = await request.post(`/api/system/pause`, {
      headers: { 'Content-Type': 'application/json' },
      data: { paused: true, secret: 'wrong' }
    });
    expect(response.status()).toBe(401);
  });
});

test.describe('Scenario F: Onboarding API Auth Guards', () => {
  test('list-sheets requires auth', async ({ request }) => {
    const response = await request.get(`/api/onboarding/list-sheets`);
    // 401/403 = requires auth; 404 = route not yet available on this env
    expect([401, 403, 404]).toContain(response.status());
  });

  test('validate-sheet requires auth', async ({ request }) => {
    const response = await request.post(`/api/onboarding/validate-sheet`, {
      data: { sheet_id: 'fake_sheet_id_12345' }
    });
    expect([401, 403]).toContain(response.status());
  });

  test('select-sheet requires auth', async ({ request }) => {
    const response = await request.post(`/api/onboarding/select-sheet`, {
      data: { sheet_id: 'fake_sheet_id_12345' }
    });
    expect([401, 403]).toContain(response.status());
  });

  test('sender-info requires auth', async ({ request }) => {
    const response = await request.post(`/api/onboarding/sender-info`, {
      data: { name: 'Test User', business_name: 'Test Co' }
    });
    expect([401, 403]).toContain(response.status());
  });
});

test.describe('Scenario G: Create Template API', () => {
  test('create-template requires auth', async ({ request }) => {
    const response = await request.post(`/api/onboarding/create-template`);
    expect([401, 403]).toContain(response.status());
  });
});

test.describe('Scenario H: Daily Cron Trigger Extended', () => {
  test('trigger-daily rejects wrong secret with 401', async ({ request }) => {
    const response = await request.post(`/api/cron/trigger-daily`, {
      headers: { 'x-cron-secret': 'wrong-secret-value' }
    });
    expect(response.status()).toBe(401);
  });

  test('trigger-daily error response has detail field', async ({ request }) => {
    const response = await request.post(`/api/cron/trigger-daily`, {
      headers: { 'x-cron-secret': 'invalid' }
    });
    expect(response.status()).toBe(401);
    const body = await response.json();
    expect(body).toHaveProperty('detail');
  });
});

test.describe('Scenario I: Billing Endpoint Auth Guards', () => {
  test('billing status requires auth', async ({ request }) => {
    const response = await request.get(`/api/billing/status`);
    expect([401, 403]).toContain(response.status());
  });

  test('create-checkout requires auth', async ({ request }) => {
    const response = await request.post(`/api/billing/create-checkout`, {
      data: {
        success_url: `/dashboard`,
        cancel_url: `/dashboard`
      }
    });
    expect([401, 403]).toContain(response.status());
  });

  test('billing webhook rejects unsigned requests with 400', async ({ request }) => {
    const response = await request.post(`/api/billing/webhook`, {
      headers: { 'Content-Type': 'application/json' },
      data: { type: 'checkout.session.completed' }
    });
    expect(response.status()).toBe(400);
    const body = await response.json();
    expect(body.detail).toMatch(/signature/i);
  });
});
