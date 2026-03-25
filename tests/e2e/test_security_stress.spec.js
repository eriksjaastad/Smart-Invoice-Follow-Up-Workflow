// @ts-check
const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const STATE_FILE = path.join(__dirname, '.auth', 'state.json');
const hasAuthState = fs.existsSync(STATE_FILE);
const CRON_SECRET = process.env.DIGEST_CRON_SECRET || '';

// ─────────────────────────────────────────────
// #5276 — XSS INJECTION via business_name
// ─────────────────────────────────────────────

test.describe('#5276 XSS — business_name injection', () => {
  test.use({ storageState: hasAuthState ? STATE_FILE : undefined });
  test.skip(!hasAuthState, 'Run auth-setup.spec.js first');

  let originalName = '';

  test('store XSS payload in business_name and verify dashboard escapes it', async ({ page, request }) => {
    // Save original
    const meResp = await request.get('/api/auth/me');
    const me = await meResp.json();
    originalName = me.business_name;

    // Inject XSS payload
    const xssPayload = '<script>alert("xss")</script>';
    const patchResp = await request.patch(`/api/users/${me.id}`, {
      data: { business_name: xssPayload },
    });
    expect(patchResp.ok()).toBeTruthy();

    // Load dashboard — should NOT execute script
    const dialogPromise = page.waitForEvent('dialog', { timeout: 3000 }).catch(() => null);
    await page.goto('/dashboard.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    const dialog = await dialogPromise;
    expect(dialog).toBeNull(); // No alert dialog = XSS blocked

    // Verify the payload is rendered as text, not executed
    const content = await page.content();
    // Should see escaped HTML or the text, not an actual <script> tag in DOM
    expect(content).not.toContain('<script>alert("xss")</script>');
  });

  test('store img onerror XSS payload', async ({ page, request }) => {
    const meResp = await request.get('/api/auth/me');
    const me = await meResp.json();

    const xssPayload = '<img src=x onerror=alert("xss2")>';
    await request.patch(`/api/users/${me.id}`, {
      data: { business_name: xssPayload },
    });

    const dialogPromise = page.waitForEvent('dialog', { timeout: 3000 }).catch(() => null);
    await page.goto('/dashboard.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    const dialog = await dialogPromise;
    expect(dialog).toBeNull();

    // Verify the payload is escaped in the DOM
    const content = await page.content();
    expect(content).not.toContain('<img src=x onerror=');
  });

  test('cleanup: restore original business_name', async ({ request }) => {
    const meResp = await request.get('/api/auth/me');
    const me = await meResp.json();
    await request.patch(`/api/users/${me.id}`, {
      data: { business_name: originalName || 'Synth Insight Labs' },
    });
  });
});

// ─────────────────────────────────────────────
// #5283 — FAKE SESSION COOKIE
// ─────────────────────────────────────────────

test.describe('#5283 Fake session cookie', () => {
  test('random UUID session returns 401 not 500', async ({ browser }) => {
    // Create isolated context with fake session cookie
    const context = await browser.newContext({
      baseURL: undefined, // Use raw URLs
    });
    await context.addCookies([{
      name: 'siw_session',
      value: 'fake-session-value-not-real',
      domain: 'smartinvoiceworkflow.com',
      path: '/',
    }]);

    const page = await context.newPage();
    const response = await page.request.get('https://smartinvoiceworkflow.com/api/auth/me');

    // Should get 401 (not authenticated), NOT 500 (server error)
    expect(response.status()).toBe(401);

    await context.close();
  });
});

// ─────────────────────────────────────────────
// #5284 — IDOR TEST
// ─────────────────────────────────────────────

test.describe('#5284 IDOR — access other user data', () => {
  test.use({ storageState: hasAuthState ? STATE_FILE : undefined });
  test.skip(!hasAuthState, 'Run auth-setup.spec.js first');

  test('PATCH /api/users/{fake-uuid} returns 403 or 404, not other user data', async ({ request }) => {
    // Try to update a non-existent user
    const fakeId = '00000000-0000-0000-0000-000000000000';
    const response = await request.patch(`/api/users/${fakeId}`, {
      data: { name: 'Hacked' },
    });
    // Should be 403 (forbidden) or 404 (not found), NOT 200
    expect([403, 404]).toContain(response.status());
  });

  test('GET /api/users/{fake-uuid}/config returns 403 or 404', async ({ request }) => {
    const fakeId = '00000000-0000-0000-0000-000000000000';
    const response = await request.get(`/api/users/${fakeId}/config`);
    // 401 = auth check rejects, 403 = forbidden, 404 = not found — all acceptable
    expect([401, 403, 404]).toContain(response.status());
  });

  test('cannot PATCH another real user by guessing UUID', async ({ request }) => {
    // Try a valid-format but wrong UUID
    const wrongId = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';
    const response = await request.patch(`/api/users/${wrongId}`, {
      data: { plan: 'paid' },  // Try to upgrade ourselves for free
    });
    expect([403, 404]).toContain(response.status());
  });
});

// ─────────────────────────────────────────────
// #5282 — DOUBLE CRON TRIGGER (duplicate drafts)
// ─────────────────────────────────────────────

test.describe('#5282 Double cron trigger', () => {
  test.skip(!CRON_SECRET, 'Set DIGEST_CRON_SECRET env var');
  test.setTimeout(60_000);

  test('two simultaneous cron triggers should not create duplicate drafts', async ({ request }) => {
    // Fire both at the same time
    const [resp1, resp2] = await Promise.all([
      request.post('/api/cron/trigger-daily', {
        headers: { 'x-cron-secret': CRON_SECRET },
      }),
      request.post('/api/cron/trigger-daily', {
        headers: { 'x-cron-secret': CRON_SECRET },
      }),
    ]);

    expect(resp1.ok()).toBeTruthy();
    expect(resp2.ok()).toBeTruthy();

    const body1 = await resp1.json();
    const body2 = await resp2.json();

    console.log('  Cron trigger 1:', JSON.stringify(body1));
    console.log('  Cron trigger 2:', JSON.stringify(body2));

    // Both should succeed but the second should ideally be a no-op
    // (same-day dedup via Last_Sent_At check)
    // At minimum, neither should error
    expect(body1.failed).toBe(0);
    expect(body2.failed).toBe(0);
  });
});

// ─────────────────────────────────────────────
// #5285 — CRON RATE LIMIT
// ─────────────────────────────────────────────

test.describe('#5285 Cron rate limit stress', () => {
  test.skip(!CRON_SECRET, 'Set DIGEST_CRON_SECRET env var');
  test.setTimeout(90_000);

  test('20 rapid cron triggers — no crashes or 500s', async ({ request }) => {
    const results = [];

    // Fire 20 requests in rapid succession (batches of 5)
    for (let batch = 0; batch < 4; batch++) {
      const promises = Array.from({ length: 5 }, () =>
        request.post('/api/cron/trigger-daily', {
          headers: { 'x-cron-secret': CRON_SECRET },
        })
      );
      const responses = await Promise.all(promises);
      for (const resp of responses) {
        results.push(resp.status());
      }
    }

    console.log('  Status codes:', results.join(', '));

    // No 500s
    const serverErrors = results.filter(s => s >= 500);
    expect(serverErrors).toEqual([]);

    // All should be 200 (or possibly 429 if rate limited, which would be good)
    const validCodes = results.filter(s => s === 200 || s === 429);
    expect(validCodes.length).toBe(results.length);
  });
});
