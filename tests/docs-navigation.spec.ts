import { test, expect } from '@playwright/test';

test('Navigate to Docs from elitea.ai home', async ({ page }) => {
  await page.goto('/');

  // The home page has a top "Docs" link that navigates to https://docs.elitea.ai/
  await page.getByRole('link', { name: /^Docs$/ }).click();

  await expect(page).toHaveURL(/docs/);
});
