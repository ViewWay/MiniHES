import type { PlaywrightTestConfig } from '@playwright/test';

import { defineConfig, devices } from '@playwright/test';

const config: PlaywrightTestConfig = defineConfig({
  testDir: '.',
  testMatch: '**/*.spec.ts',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'test-results/html' }],
  ],
  timeout: 30_000,
  expect: {
    timeout: 5_000,
    toHaveScreenshot: { maxDiffPixelRatio: 0.01 },
  },
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:5666',
    actionTimeout: 10_000,
    headless: !!process.env.CI,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  snapshotDir: './snapshots',
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'visual',
      testDir: './visual',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});

export default config;
