import { test, expect } from '@playwright/test';

const menuItems = [
  { menuItem: 'Browser Windows', expectedHeading: 'Browser Windows', expectedPath: '/browser-windows' },
  { menuItem: 'Alerts', expectedHeading: 'Alerts', expectedPath: '/alerts' },
  { menuItem: 'Frames', expectedHeading: 'Frames', expectedPath: '/frames' },
  { menuItem: 'Nested Frames', expectedHeading: 'Nested Frames', expectedPath: '/nestedframes' },
  { menuItem: 'Modal Dialogs', expectedHeading: 'Modal Dialogs', expectedPath: '/modal-dialogs' },
] as const;

test.describe('DemoQA - Alerts, Frame & Windows: left navigation + Browser Windows controls', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/alertsWindows');
  });

  test('Navigate to each feature page from left navigation menu', async ({ page }) => {
    const leftNav = page.locator('.left-pannel');
    await expect(leftNav).toBeVisible();

    for (const item of menuItems) {
      await page.getByRole('link', { name: item.menuItem, exact: true }).click();
      await expect(page).toHaveURL(new RegExp(`${item.expectedPath.replace('/', '\\/')}$`));
      await expect(page.getByRole('heading', { name: item.expectedHeading, exact: true })).toBeVisible();
    }
  });

  test('Browser Windows page shows controls to open tabs/windows', async ({ page }) => {
    await page.getByRole('link', { name: 'Browser Windows', exact: true }).click();

    await expect(page).toHaveURL(/\/browser-windows$/);
    await expect(page.getByRole('heading', { name: 'Browser Windows', exact: true })).toBeVisible();

    await expect(page.getByRole('button', { name: 'New Tab', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'New Window', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'New Window Message', exact: true })).toBeVisible();
  });
});
