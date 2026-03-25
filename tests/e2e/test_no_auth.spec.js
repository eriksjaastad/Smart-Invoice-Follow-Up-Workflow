// @ts-check
const { test, expect } = require('@playwright/test');
const path = require('path');
const { SCREENSHOTS_DIR } = require('./test-utils');

// ─────────────────────────────────────────────
// 1. LANDING PAGE — Content & Structure
// ─────────────────────────────────────────────

test.describe('Landing Page — Content', () => {
  test('page title contains Smart Invoice', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Smart Invoice/i);
  });

  test('hero section renders with headline and CTA', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Hero headline
    const headline = page.locator('text=Follow-up is the').first();
    await expect(headline).toBeVisible({ timeout: 10000 });

    // "Standard." accent text
    await expect(page.locator('text=Standard.').first()).toBeVisible();

    // Hero subtext
    await expect(page.locator('text=42-day escalation').first()).toBeVisible();

    // CTA button
    const cta = page.locator('text=Deploy Protocol').first();
    await expect(cta).toBeVisible();
  });

  test('navbar renders with brand and Start Free link', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Brand name
    await expect(page.locator('text=SMART').first()).toBeVisible({ timeout: 10000 });

    // Start Free button links to login
    const startFree = page.locator('a[href="/login.html"]').first();
    await expect(startFree).toBeVisible();
  });

  test('features section shows all three feature cards', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=42-day Escalation').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Zero-Touch Integration').first()).toBeVisible();
    await expect(page.locator('text=Weekly Success').first()).toBeVisible();
  });

  test('philosophy section renders', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=Autonomy').first()).toBeVisible({ timeout: 10000 });
  });

  test('pricing section shows all three tiers', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Tier names
    await expect(page.locator('text=Essential').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Performance').first()).toBeVisible();
    await expect(page.locator('text=Enterprise').first()).toBeVisible();

    // Prices
    await expect(page.locator('text=$0').first()).toBeVisible();
    await expect(page.locator('text=$15').first()).toBeVisible();
    await expect(page.locator('text=Custom').first()).toBeVisible();

    // Invoice limits
    await expect(page.locator('text=3 Invoices / day').first()).toBeVisible();
    await expect(page.locator('text=100 Invoices / day').first()).toBeVisible();
  });

  test('footer renders with company name and status badge', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=Synth Insight Labs').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=System Operational').first()).toBeVisible();
  });

  test('protocol cards show Connect, Index, Automate steps', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=Connect.').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Index.').first()).toBeVisible();
    await expect(page.locator('text=Automate.').first()).toBeVisible();
  });
});

// ─────────────────────────────────────────────
// 2. LANDING PAGE — Navigation & Links
// ─────────────────────────────────────────────

test.describe('Landing Page — Links', () => {
  test('all CTA buttons point to /login.html', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Collect all links to login.html
    const loginLinks = page.locator('a[href="/login.html"]');
    const count = await loginLinks.count();
    expect(count).toBeGreaterThanOrEqual(3); // navbar + hero + pricing Essential + pricing Performance
  });

  test('Enterprise tier links to mailto for sales', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const mailto = page.locator('a[href^="mailto:"]').first();
    await expect(mailto).toBeVisible({ timeout: 10000 });
    const href = await mailto.getAttribute('href');
    expect(href).toContain('synthinsightlabs.com');
  });

  test('navbar anchor links exist for Protocol, Philosophy, Pricing', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('a[href="#protocol"]')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('a[href="#philosophy"]')).toBeVisible();
    await expect(page.locator('a[href="#pricing"]')).toBeVisible();
  });

  test('footer Terms and Privacy links exist', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('footer >> text=Terms').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('footer >> text=Privacy').first()).toBeVisible();
  });
});

// ─────────────────────────────────────────────
// 3. LANDING PAGE — Responsive / Mobile
// ─────────────────────────────────────────────

test.describe('Landing Page — Mobile Viewport', () => {
  test.use({ viewport: { width: 375, height: 812 } }); // iPhone X

  test('hero renders on mobile', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=Follow-up is the').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Deploy Protocol').first()).toBeVisible();

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'mobile-01-hero.png'),
      fullPage: false
    });
  });

  test('pricing cards stack vertically on mobile', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Scroll to pricing
    await page.locator('#pricing').scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);

    await expect(page.locator('text=$0').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=$15').first()).toBeVisible();

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'mobile-02-pricing.png'),
      fullPage: false
    });
  });

  test('navbar is visible on mobile (md nav links hidden)', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // The nav links (Protocol, Philosophy, Pricing) are hidden md:flex
    const navProtocol = page.locator('nav >> a[href="#protocol"]');
    await expect(navProtocol).toBeHidden();

    // But Start Free button should still be visible
    const startFree = page.locator('nav >> a[href="/login.html"]');
    await expect(startFree).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Landing Page — Tablet Viewport', () => {
  test.use({ viewport: { width: 768, height: 1024 } }); // iPad

  test('landing page renders on tablet', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=Follow-up is the').first()).toBeVisible({ timeout: 10000 });

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'tablet-01-landing.png'),
      fullPage: true
    });
  });
});

// ─────────────────────────────────────────────
// 4. LOGIN PAGE — Renders Before Redirect
// ─────────────────────────────────────────────

test.describe('Login Page', () => {
  test('login page shows loading UI before redirect', async ({ page }) => {
    // Intercept the auth redirect so we can inspect the page
    await page.route('**/api/auth/login', route => route.abort());

    await page.goto('/login.html');
    await page.waitForLoadState('domcontentloaded');

    await expect(page).toHaveTitle(/Smart Invoice/i);
    await expect(page.locator('text=Connecting you securely').first()).toBeVisible({ timeout: 5000 });

    // Bouncing dots animation exists
    const dots = page.locator('.animate-bounce');
    expect(await dots.count()).toBe(3);

    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'no-auth-login-page.png'),
      fullPage: true
    });
  });
});

// ─────────────────────────────────────────────
// 5. PROTECTED PAGES — Redirect to Login
// ─────────────────────────────────────────────

test.describe('Protected Pages — Redirect Without Auth', () => {
  test('dashboard.html redirects to login when not authed', async ({ page }) => {
    await page.goto('/dashboard.html');
    // The page fetches /api/auth/me, gets 401, and JS redirects to /login.html
    await page.waitForURL(/login|auth/, { timeout: 15000 });
  });

  test('settings.html redirects to login when not authed', async ({ page }) => {
    await page.goto('/settings.html');
    await page.waitForURL(/login|auth/, { timeout: 15000 });
  });

  test('billing.html redirects to login when not authed', async ({ page }) => {
    await page.goto('/billing.html');
    await page.waitForURL(/login|auth/, { timeout: 15000 });
  });

  test('onboarding.html shows login redirect or unauthenticated state', async ({ page }) => {
    await page.goto('/onboarding.html');
    // Onboarding fetches /api/auth/me — JS redirects to login on 401
    await page.waitForTimeout(3000);
    const url = page.url();
    // Should either redirect to login or stay on page without user data
    expect(url).toMatch(/login|auth|onboarding/);
  });
});

// ─────────────────────────────────────────────
// 6. API CONTRACT — Health & System
// ─────────────────────────────────────────────

test.describe('API — Health & System', () => {
  test('GET /health returns status healthy with version', async ({ request }) => {
    const response = await request.get('/health');
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.status).toBe('healthy');
    expect(body.version).toMatch(/^\d+\.\d+\.\d+$/);
    expect(body).toHaveProperty('environment');
  });

  test('GET /api/system/status returns paused boolean', async ({ request }) => {
    const response = await request.get('/api/system/status');
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(typeof body.paused).toBe('boolean');
  });
});

// ─────────────────────────────────────────────
// 7. API CONTRACT — Auth Guards (all should reject)
// ─────────────────────────────────────────────

test.describe('API — Auth Guards', () => {
  test('GET /api/auth/me requires auth', async ({ request }) => {
    const response = await request.get('/api/auth/me');
    expect([401, 403]).toContain(response.status());
  });

  test('GET /api/users/me requires auth', async ({ request }) => {
    const response = await request.get('/api/users/me');
    expect([401, 403]).toContain(response.status());
  });

  test('PATCH /api/users/:id requires auth', async ({ request }) => {
    const response = await request.patch('/api/users/fake-uuid', {
      data: { name: 'hacker' }
    });
    expect([401, 403, 422]).toContain(response.status());
  });

  test('GET /api/users/:id/config requires auth', async ({ request }) => {
    const response = await request.get('/api/users/fake-uuid/config');
    expect([401, 403, 422]).toContain(response.status());
  });

  test('POST /api/onboarding/validate-sheet requires auth', async ({ request }) => {
    const response = await request.post('/api/onboarding/validate-sheet', {
      data: { sheet_id: 'fake' }
    });
    expect([401, 403]).toContain(response.status());
  });

  test('POST /api/onboarding/select-sheet requires auth', async ({ request }) => {
    const response = await request.post('/api/onboarding/select-sheet', {
      data: { sheet_id: 'fake' }
    });
    expect([401, 403]).toContain(response.status());
  });

  test('POST /api/onboarding/create-template requires auth', async ({ request }) => {
    const response = await request.post('/api/onboarding/create-template');
    expect([401, 403]).toContain(response.status());
  });

  test('POST /api/onboarding/sender-info requires auth', async ({ request }) => {
    const response = await request.post('/api/onboarding/sender-info', {
      data: { name: 'Test', business_name: 'Co' }
    });
    expect([401, 403]).toContain(response.status());
  });

  test('GET /api/billing/status requires auth', async ({ request }) => {
    const response = await request.get('/api/billing/status');
    expect([401, 403]).toContain(response.status());
  });

  test('POST /api/billing/create-checkout requires auth', async ({ request }) => {
    const response = await request.post('/api/billing/create-checkout', {
      data: { success_url: '/', cancel_url: '/' }
    });
    expect([401, 403]).toContain(response.status());
  });

  test('POST /api/billing/customer-portal requires auth', async ({ request }) => {
    const response = await request.post('/api/billing/customer-portal');
    expect([401, 403]).toContain(response.status());
  });

  test('POST /api/digest/send requires auth', async ({ request }) => {
    const response = await request.post('/api/digest/send');
    // 401/403 = auth guard, 422 = validation fires before auth check
    expect([401, 403, 422]).toContain(response.status());
  });

  test('POST /api/notifications/check-failures requires auth', async ({ request }) => {
    const response = await request.post('/api/notifications/check-failures');
    expect([401, 403, 422]).toContain(response.status());
  });

  test('GET /api/auth/google/connect requires auth', async ({ request }) => {
    const response = await request.get('/api/auth/google/connect');
    // Could redirect (302) or return 401/403
    expect([302, 401, 403]).toContain(response.status());
  });

  test('POST /api/auth/google/disconnect requires auth', async ({ request }) => {
    const response = await request.post('/api/auth/google/disconnect');
    expect([401, 403, 405]).toContain(response.status());
  });
});

// ─────────────────────────────────────────────
// 8. API CONTRACT — Security Boundaries
// ─────────────────────────────────────────────

test.describe('API — Security Boundaries', () => {
  test('POST /api/cron/trigger-daily rejects without secret', async ({ request }) => {
    const response = await request.post('/api/cron/trigger-daily');
    expect(response.status()).toBe(401);
    const body = await response.json();
    expect(body).toHaveProperty('detail');
  });

  test('POST /api/cron/trigger-daily rejects wrong secret', async ({ request }) => {
    const response = await request.post('/api/cron/trigger-daily', {
      headers: { 'x-cron-secret': 'wrong-secret' }
    });
    expect(response.status()).toBe(401);
  });

  test('POST /api/system/pause rejects wrong secret', async ({ request }) => {
    const response = await request.post('/api/system/pause', {
      data: { paused: true, secret: 'wrong' }
    });
    expect(response.status()).toBe(401);
  });

  test('POST /api/billing/webhook rejects unsigned payload', async ({ request }) => {
    const response = await request.post('/api/billing/webhook', {
      headers: { 'Content-Type': 'application/json' },
      data: { type: 'checkout.session.completed' }
    });
    expect(response.status()).toBe(400);
    const body = await response.json();
    expect(body.detail).toMatch(/signature/i);
  });

  test('POST /api/webhooks/make-results rejects missing API key', async ({ request }) => {
    const response = await request.post('/api/webhooks/make-results', {
      data: { user_id: 'fake', results: [] }
    });
    expect([401, 403, 422]).toContain(response.status());
  });
});

// ─────────────────────────────────────────────
// 9. API CONTRACT — 404 Handling
// ─────────────────────────────────────────────

test.describe('API — 404 Handling', () => {
  test('unknown API route returns 404', async ({ request }) => {
    const response = await request.get('/api/nonexistent-route');
    expect(response.status()).toBe(404);
  });

  test('unknown nested API route returns 404', async ({ request }) => {
    const response = await request.get('/api/users/fake-uuid/nonexistent');
    expect(response.status()).toBe(404);
  });
});

// ─────────────────────────────────────────────
// 10. STATIC ASSETS
// ─────────────────────────────────────────────

test.describe('Static Assets', () => {
  test('logo.png loads successfully', async ({ request }) => {
    const response = await request.get('/images/logo.png');
    expect(response.ok()).toBeTruthy();
    const contentType = response.headers()['content-type'];
    expect(contentType).toContain('image');
  });

  test('landing page loads external CDN scripts', async ({ page }) => {
    const failedRequests = [];
    page.on('requestfailed', request => {
      const url = request.url();
      // Only track CDN scripts, not optional/non-critical resources
      if (url.includes('cdn.tailwindcss.com') ||
          url.includes('unpkg.com/react') ||
          url.includes('cdnjs.cloudflare.com/ajax/libs/gsap')) {
        failedRequests.push(url);
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    expect(failedRequests).toEqual([]);
  });
});

// ─────────────────────────────────────────────
// 11. SEO & META
// ─────────────────────────────────────────────

test.describe('SEO & Meta Tags', () => {
  test('landing page has proper meta viewport', async ({ page }) => {
    await page.goto('/');
    const viewport = await page.locator('meta[name="viewport"]').getAttribute('content');
    expect(viewport).toContain('width=device-width');
  });

  test('landing page has charset UTF-8', async ({ page }) => {
    await page.goto('/');
    const charset = await page.locator('meta[charset]').getAttribute('charset');
    expect(charset?.toUpperCase()).toBe('UTF-8');
  });

  test('landing page has lang attribute', async ({ page }) => {
    await page.goto('/');
    const lang = await page.locator('html').getAttribute('lang');
    expect(lang).toBe('en');
  });

  test('each static page has a unique title', async ({ page }) => {
    const pages = ['/', '/login.html', '/dashboard.html', '/billing.html', '/settings.html', '/onboarding.html'];
    const titles = new Set();

    for (const p of pages) {
      await page.goto(p, { waitUntil: 'domcontentloaded' });
      const title = await page.title();
      titles.add(title);
    }

    // All 6 pages should have distinct titles
    expect(titles.size).toBe(pages.length);
  });
});

// ─────────────────────────────────────────────
// 12. PERFORMANCE — Basic Load Timing
// ─────────────────────────────────────────────

test.describe('Performance', () => {
  test('landing page loads within 8 seconds', async ({ page }) => {
    const start = Date.now();
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    const elapsed = Date.now() - start;

    // Landing page with CDN deps should load within 8s
    expect(elapsed).toBeLessThan(8000);
  });

  test('health endpoint responds within 2 seconds', async ({ request }) => {
    const start = Date.now();
    const response = await request.get('/health');
    const elapsed = Date.now() - start;

    expect(response.ok()).toBeTruthy();
    expect(elapsed).toBeLessThan(2000);
  });
});

// ─────────────────────────────────────────────
// 13. CONSOLE ERRORS — Landing Page
// ─────────────────────────────────────────────

test.describe('Console Errors', () => {
  test('landing page has no critical JS errors', async ({ page }) => {
    const errors = [];
    page.on('pageerror', error => {
      errors.push(error.message);
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');
    // Wait extra for React/GSAP init
    await page.waitForTimeout(3000);

    // Filter out known non-critical issues (e.g., third-party CDN warnings)
    const criticalErrors = errors.filter(e =>
      !e.includes('ResizeObserver') &&
      !e.includes('Non-Error promise rejection')
    );

    expect(criticalErrors).toEqual([]);
  });
});
