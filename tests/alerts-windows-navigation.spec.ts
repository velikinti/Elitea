import { test, expect } from '@playwright/test';

const menuItems = [
  { menu: 'Browser Windows', expectedHeading: 'Browser Windows', expectedPath: '/browser-windows' },
  { menu: 'Alerts', expectedHeading: 'Alerts', expectedPath: '/alerts' },
  { menu: 'Frames', expectedHeading: 'Frames', expectedPath: '/frames' },
  { menu: 'Nested Frames', expectedHeading: 'Nested Frames', expectedPath: '/nestedframes' },
  { menu: 'Modal Dialogs', expectedHeading: 'Modal Dialogs', expectedPath: '/modal-dialogs' },
] as const;

test.describe('DemoQA - Alerts, Frame & Windows: left navigation + key UI checks', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/alertsWindows');
    await expect(page.getByText('Please select an item from left to start practice.')).toBeVisible();
    await expect(page.getByRole('link', { name: 'Alerts, Frame & Windows' })).toBeVisible();
  });

  test('Navigate to a feature page from the left navigation menu (table-driven)', async ({ page }) => {
    for (const item of menuItems) {
      await test.step(`Navigate to: ${item.menu}`, async () => {
        await page.getByRole('link', { name: item.menu, exact: true }).click();
        await expect(page).toHaveURL(new RegExp(`${item.expectedPath.replace('/', '\\/')}$`));
        await expect(page.getByRole('heading', { name: item.expectedHeading, level: 1 })).toBeVisible();
      });
    }
  });

  test('Browser Windows page shows controls to open tabs/windows', async ({ page }) => {
    await page.getByRole('link', { name: 'Browser Windows', exact: true }).click();
    await expect(page).toHaveURL(/\/browser-windows$/);

    await expect(page.getByRole('heading', { name: 'Browser Windows', level: 1 })).toBeVisible();
    await expect(page.getByRole('button', { name: 'New Tab' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'New Window' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'New Window Message' })).toBeVisible();
  });

  test('Active menu item is visually indicated (if implemented)', async ({ page }) => {
    const alertsNav = page.getByRole('link', { name: 'Alerts', exact: true });
    await alertsNav.click();
    await expect(page).toHaveURL(/\/alerts$/);

    // DemoQA marks active sidebar item with an 'active' class
    await expect(alertsNav).toHaveClass(/active/);
  });

  test('Left navigation remains usable when content requires scrolling', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 450 });

    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));

    // Sidebar should still be interactable while scrolled
    await page.getByRole('link', { name: 'Modal Dialogs', exact: true }).click();
    await expect(page).toHaveURL(/\/modal-dialogs$/);
    await expect(page.getByRole('heading', { name: 'Modal Dialogs', level: 1 })).toBeVisible();
  });

  test('Clicking a left menu item navigates (broken link detection)', async ({ page }) => {
    await page.getByRole('link', { name: 'Alerts', exact: true }).click();

    // If this fails and URL/content does not change, treat as defect.
    await expect(page).toHaveURL(/\/alerts$/);
    await expect(page.getByRole('heading', { name: 'Alerts', level: 1 })).toBeVisible();
  });
});
