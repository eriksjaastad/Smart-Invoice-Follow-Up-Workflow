// @ts-check
const { defineConfig } = require('@playwright/test');

// Support multi-environment testing
const BASE_URL = process.env.PREVIEW_URL
  || (process.env.TEST_ENV === 'production'
      ? 'https://smartinvoiceworkflow.com'
      : 'https://smartinvoiceworkflow.com'); // default to prod

module.exports = defineConfig({
  testDir: './tests/e2e',
  timeout: 30000,
  retries: 1,
  use: {
    baseURL: BASE_URL,
    headless: true,
    screenshot: 'on', // Changed from 'only-on-failure' to capture all screenshots
    trace: 'on-first-retry',
    viewport: { width: 1280, height: 720 }, // Standard viewport for consistent screenshots
    // Bypass Vercel Deployment Protection for Preview environments
    extraHTTPHeaders: {
      'x-vercel-protection-bypass': process.env.VERCEL_AUTOMATION_BYPASS_SECRET || '',
    },
  },
  reporter: [['list'], ['html', { outputFolder: 'tests/e2e/report' }]],
});
