import { test, expect } from '@playwright/test';

test('EPAM: navigate Services -> Explore Our Client Work and verify Client Work header', async ({ page }) => {
  await page.goto('/');

  // Header menu (hamburger) is used on smaller viewports; click if Services isn't visible.
  const servicesLink = page.getByRole('link', { name: 'Services', exact: true });
  if (!(await servicesLink.isVisible().catch(() => false))) {
    await page.getByRole('button').first().click();
  }

  await page.getByRole('link', { name: 'Services', exact: true }).click();
  await expect(page).toHaveURL(/\/services/);

  await page.getByRole('link', { name: 'Explore Our Client Work' }).click();
  await expect(page).toHaveURL(/\/services\/client-work/);

  await expect(page.getByRole('heading', { name: 'Client Work' })).toBeVisible();
});
