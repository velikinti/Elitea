import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: 'https://demowebshop.tricentis.com',
    trace: 'on-first-retry',
  },
});
