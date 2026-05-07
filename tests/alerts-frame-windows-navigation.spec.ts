import { test, expect } from '@playwright/test';

const cases = [
  { menuItem: 'Browser Windows', expectedHeading: 'Browser Windows', expectedPath: '/browser-windows' },
  { menuItem: 'Alerts', expectedHeading: 'Alerts', expectedPath: '/alerts' },
  { menuItem: 'Frames', expectedHeading: 'Frames', expectedPath: '/frames' },
  { menuItem: 'Nested Frames', expectedHeading: 'Nested Frames', expectedPath: '/nestedframes' },
  { menuItem: 'Modal Dialogs', expectedHeading: 'Modal Dialogs', expectedPath: '/modal-dialogs' },
] as const;

test.describe('Alerts, Frame & Windows: left navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/alertsWindows');

    // Ensure left navigation is visible
    await expect(page.getByText('Alerts, Frame & Windows', { exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Browser Windows' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Alerts' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Frames', exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Nested Frames' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Modal Dialogs' })).toBeVisible();
  });

  for (const c of cases) {
    test(`Navigate via left menu: ${c.menuItem} -> ${c.expectedHeading}`, async ({ page }) => {
      await page.getByRole('link', { name: c.menuItem }).click();

      await expect(page).toHaveURL(new RegExp(`${c.expectedPath.replace('/', '\\/')}$`));
      await expect(page.getByRole('heading', { name: c.expectedHeading, level: 1 })).toBeVisible();
    });
  }

  test('Browser Windows page shows controls to open tabs/windows', async ({ page }) => {
    await page.getByRole('link', { name: 'Browser Windows' }).click();
    await expect(page.getByRole('heading', { name: 'Browser Windows', level: 1 })).toBeVisible();

    await expect(page.getByRole('button', { name: 'New Tab' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'New Window' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'New Window Message' })).toBeVisible();
  });
});
