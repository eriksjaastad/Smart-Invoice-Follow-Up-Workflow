// @ts-check
const { test, expect } = require('@playwright/test');
const path = require('path');

const SCREENSHOTS_DIR = path.join(__dirname, 'screenshots');

/**
 * Visual Snapshot Test Suite
 * 
 * Purpose: Capture screenshots of every accessible page for visual review.
 * This suite does NOT assert layout details - it's purely for visual documentation.
 * 
 * Screenshots are saved to tests/e2e/screenshots/ with numbered descriptive names.
 */

test.describe('Visual Snapshots - Public Pages', () => {
  test('01 - Landing page hero section', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Wait for page to be fully loaded (just wait for body)
    await page.waitForTimeout(2000);

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, '01-landing-hero.png'),
      fullPage: true
    });
  });

  test('02 - Landing page pricing section', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Scroll to pricing section
    const pricingSection = page.locator('text=Free').first();
    await pricingSection.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500); // Let scroll animation complete
    
    await page.screenshot({ 
      path: path.join(SCREENSHOTS_DIR, '02-pricing-section.png'), 
      fullPage: true 
    });
  });

  test('03 - Landing page footer', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Scroll to bottom
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);
    
    await page.screenshot({ 
      path: path.join(SCREENSHOTS_DIR, '03-landing-footer.png'), 
      fullPage: true 
    });
  });
});

test.describe('Visual Snapshots - Authentication Flow', () => {
  test('04 - Login page initial state', async ({ page }) => {
    await page.goto(`/login.html`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000); // Wait for any redirects
    
    await page.screenshot({ 
      path: path.join(SCREENSHOTS_DIR, '04-login-page.png'), 
      fullPage: true 
    });
  });

  test('05 - Auth0 redirect or mock auth', async ({ page }) => {
    await page.goto(`/api/auth/login`);
    await page.waitForTimeout(2000); // Wait for redirect
    
    await page.screenshot({ 
      path: path.join(SCREENSHOTS_DIR, '05-auth-redirect.png'), 
      fullPage: true 
    });
  });

  test('06 - Dashboard after login (mock auth)', async ({ page }) => {
    // Use mock auth to get to dashboard
    await page.goto(`/api/auth/login`);
    await page.waitForURL(/dashboard/, { timeout: 15000 });
    await page.waitForLoadState('networkidle');
    
    await page.screenshot({ 
      path: path.join(SCREENSHOTS_DIR, '06-dashboard-main.png'), 
      fullPage: true 
    });
  });
});

test.describe('Visual Snapshots - Onboarding Flow', () => {
  test('07 - Onboarding step 1 - Connect Google', async ({ page }) => {
    // Login first
    await page.goto(`/api/auth/login`);
    await page.waitForURL(/dashboard/, { timeout: 15000 });
    
    // Navigate to onboarding
    await page.goto(`/onboarding.html`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    
    await page.screenshot({ 
      path: path.join(SCREENSHOTS_DIR, '07-onboarding-step1.png'), 
      fullPage: true 
    });
  });

  test('08 - Onboarding step 2 - Select sheet', async ({ page }) => {
    await page.goto(`/api/auth/login`);
    await page.waitForURL(/dashboard/, { timeout: 15000 });
    
    await page.goto(`/onboarding.html`);
    await page.waitForLoadState('networkidle');
    
    // Try to navigate to step 2 if there's a next button
    const nextButton = page.locator('button:has-text("Next")').or(page.locator('button:has-text("Continue")'));
    if (await nextButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await nextButton.first().click();
      await page.waitForTimeout(1000);
    }
    
    await page.screenshot({ 
      path: path.join(SCREENSHOTS_DIR, '08-onboarding-step2.png'), 
      fullPage: true 
    });
  });

  test('09 - Onboarding step 3 - Sender info', async ({ page }) => {
    await page.goto(`/api/auth/login`);
    await page.waitForURL(/dashboard/, { timeout: 15000 });
    
    await page.goto(`/onboarding.html`);
    await page.waitForLoadState('networkidle');
    
    // Try to navigate through steps
    for (let i = 0; i < 2; i++) {
      const nextButton = page.locator('button:has-text("Next")').or(page.locator('button:has-text("Continue")'));
      if (await nextButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await nextButton.first().click();
        await page.waitForTimeout(1000);
      }
    }
    
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, '09-onboarding-step3.png'),
      fullPage: true
    });
  });
});

test.describe('Visual Snapshots - Dashboard Views', () => {
  test('10 - Dashboard overview', async ({ page }) => {
    await page.goto(`/api/auth/login`);
    await page.waitForURL(/dashboard/, { timeout: 15000 });
    await page.waitForLoadState('networkidle');

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, '10-dashboard-overview.png'),
      fullPage: true
    });
  });

  test('11 - Dashboard settings panel (if exists)', async ({ page }) => {
    await page.goto(`/api/auth/login`);
    await page.waitForURL(/dashboard/, { timeout: 15000 });
    await page.waitForLoadState('networkidle');

    // Try to find and click settings button
    const settingsButton = page.locator('button:has-text("Settings")').or(
      page.locator('a:has-text("Settings")')
    ).or(
      page.locator('[aria-label="Settings"]')
    );

    if (await settingsButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await settingsButton.first().click();
      await page.waitForTimeout(1000);
    }

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, '11-dashboard-settings.png'),
      fullPage: true
    });
  });

  test('12 - Dashboard user menu', async ({ page }) => {
    await page.goto(`/api/auth/login`);
    await page.waitForURL(/dashboard/, { timeout: 15000 });
    await page.waitForLoadState('networkidle');

    // Try to find and click user menu
    const userMenu = page.locator('[aria-label="User menu"]').or(
      page.locator('button:has-text("Mock")') // Mock user name
    ).or(
      page.locator('[data-testid="user-menu"]')
    );

    if (await userMenu.isVisible({ timeout: 2000 }).catch(() => false)) {
      await userMenu.first().click();
      await page.waitForTimeout(500);
    }

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, '12-dashboard-user-menu.png'),
      fullPage: true
    });
  });
});

test.describe('Visual Snapshots - Billing Flow', () => {
  test('13 - Billing page or upgrade button', async ({ page }) => {
    await page.goto(`/api/auth/login`);
    await page.waitForURL(/dashboard/, { timeout: 15000 });
    await page.waitForLoadState('networkidle');

    // Try to navigate to billing page
    const billingLink = page.locator('a:has-text("Billing")').or(
      page.locator('a:has-text("Upgrade")').or(
        page.locator('a[href*="billing"]')
      )
    );

    if (await billingLink.isVisible({ timeout: 2000 }).catch(() => false)) {
      await billingLink.first().click();
      await page.waitForTimeout(1000);
    }

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, '13-billing-page.png'),
      fullPage: true
    });
  });

  test('14 - Stripe checkout redirect (test mode)', async ({ page }) => {
    await page.goto(`/api/auth/login`);
    await page.waitForURL(/dashboard/, { timeout: 15000 });

    // Look for upgrade/subscribe button
    const upgradeBtn = page.locator('button:has-text("Upgrade")').or(
      page.locator('button:has-text("Subscribe")').or(
        page.locator('button:has-text("Pro")')
      )
    );

    if (await upgradeBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await upgradeBtn.first().click();

      // Wait for Stripe redirect or modal
      await page.waitForTimeout(3000);

      await page.screenshot({
        path: path.join(SCREENSHOTS_DIR, '14-stripe-checkout.png'),
        fullPage: true
      });
    } else {
      // No upgrade button found, just capture current state
      await page.screenshot({
        path: path.join(SCREENSHOTS_DIR, '14-no-upgrade-button.png'),
        fullPage: true
      });
    }
  });
});

test.describe('Visual Snapshots - Error States', () => {
  test('15 - 404 page', async ({ page }) => {
    await page.goto(`/nonexistent-page-12345`);
    await page.waitForLoadState('networkidle');

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, '15-404-page.png'),
      fullPage: true
    });
  });

  test('16 - Unauthorized API access', async ({ page }) => {
    // Try to access protected endpoint without auth
    const response = await page.goto(`/api/billing/status`);
    await page.waitForLoadState('networkidle');

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, '16-unauthorized-api.png'),
      fullPage: true
    });
  });
});

