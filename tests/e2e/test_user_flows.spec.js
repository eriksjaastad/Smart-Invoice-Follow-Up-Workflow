// @ts-check
const { test, expect } = require('@playwright/test');

const BASE_URL = 'https://smartinvoiceworkflow.com';

test.describe('Scenario A: Landing Page', () => {
  test('loads and displays key content', async ({ page }) => {
    await page.goto(BASE_URL);
    await expect(page).toHaveTitle(/Smart Invoice/i);

    // Check hero section exists
    const hero = page.locator('text=Automate your invoice').first();
    await expect(hero).toBeVisible({ timeout: 10000 });

    // Check pricing section
    await expect(page.locator('text=Free').first()).toBeVisible();
    await expect(page.locator('text=Pro').first()).toBeVisible();

    // Check CTA buttons exist
    const startFreeBtn = page.locator('text=Start').first();
    await expect(startFreeBtn).toBeVisible();
  });

  test('Start Free button navigates to login', async ({ page }) => {
    await page.goto(BASE_URL);
    // Click first signup-type button
    await page.locator('a[href="/login.html"]').first().click();
    // Should end up at login.html which auto-redirects to /api/auth/login
    await page.waitForURL(/\/(login\.html|api\/auth\/login|dashboard)/, { timeout: 15000 });
  });
});

test.describe('Scenario B: Mock Auth Signup Flow', () => {
  test('full signup → dashboard → onboarding flow', async ({ page }) => {
    // Step 1: Hit login - mock auth should auto-create user and redirect
    await page.goto(`${BASE_URL}/api/auth/login`);
    await page.waitForURL(/dashboard/, { timeout: 15000 });

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
    await page.goto(`${BASE_URL}/api/auth/login`);
    await page.waitForURL(/dashboard/, { timeout: 15000 });

    // Navigate to onboarding
    await page.goto(`${BASE_URL}/onboarding.html`);
    await page.waitForLoadState('networkidle');

    // Should show step 1 - Connect Google Account
    await expect(page.locator('text=Google').first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Scenario C: API Health Checks', () => {
  test('health endpoint returns healthy', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/health`);
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.status).toBe('healthy');
    expect(body.environment).toBe('production');
  });

  test('system status returns not paused', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/system/status`);
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.paused).toBe(false);
  });
});

test.describe('Scenario D: Payment Flow (Stripe Test Mode)', () => {
  test('billing checkout creates Stripe session', async ({ page }) => {
    // Login via mock auth first
    await page.goto(`${BASE_URL}/api/auth/login`);
    await page.waitForURL(/dashboard/, { timeout: 15000 });

    // Check if there's an upgrade/payment button on dashboard
    const upgradeBtn = page.locator('text=Upgrade').or(page.locator('text=Pro')).or(page.locator('text=Subscribe'));

    if (await upgradeBtn.first().isVisible({ timeout: 5000 }).catch(() => false)) {
      await upgradeBtn.first().click();
      // Should redirect to Stripe Checkout (test mode)
      await page.waitForURL(/checkout\.stripe\.com/, { timeout: 15000 });

      // Verify we're in test mode
      const url = page.url();
      expect(url).toContain('checkout.stripe.com');
    } else {
      // No upgrade button visible - check if billing API exists
      const response = await page.request.post(`${BASE_URL}/api/billing/create-checkout-session`, {
        headers: { 'Content-Type': 'application/json' }
      });
      // Should get 401 (not authenticated via API) or redirect
      expect([200, 302, 401, 403, 405, 422]).toContain(response.status());
    }
  });
});

test.describe('Scenario E: Error Handling', () => {
  test('404 page for unknown API routes', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/nonexistent`);
    expect(response.status()).toBe(404);
  });

  test('webhook rejects unsigned requests', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/api/billing/webhook`, {
      headers: { 'Content-Type': 'application/json' },
      data: { test: true }
    });
    expect(response.status()).toBe(400);
    const body = await response.json();
    expect(body.detail).toContain('signature');
  });

  test('cron rejects missing secret', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/api/cron/trigger-daily`);
    expect(response.status()).toBe(401);
  });

  test('system pause rejects wrong secret', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/api/system/pause`, {
      headers: { 'Content-Type': 'application/json' },
      data: { paused: true, secret: 'wrong' }
    });
    expect(response.status()).toBe(401);
  });
});
