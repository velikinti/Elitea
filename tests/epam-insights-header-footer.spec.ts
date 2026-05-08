import { test, expect, type Page } from '@playwright/test';

const INSIGHTS_URL = 'https://www.epam.com/insights';

async function ensureHamburgerMenuOpen(page: Page) {
  // On some viewports the main navigation is collapsed behind a hamburger button.
  const banner = page.getByRole('banner');
  const menuToggle = banner.getByRole('button').first();
  const mainNav = banner.getByRole('navigation', { name: 'Main navigation' }).first();

  // If main nav links are not visible, open hamburger.
  const aboutLink = mainNav.getByRole('link', { name: /^About$/ }).first();
  if (!(await aboutLink.isVisible().catch(() => false))) {
    await menuToggle.click();
  }
}

test.describe('EPAM Insights - global header & footer navigation', () => {
  test('Navigate to About from Insights using header navigation; header remains usable', async ({ page }) => {
    await page.goto(INSIGHTS_URL, { waitUntil: 'domcontentloaded' });

    // Header is visible
    await expect(page.getByRole('banner')).toBeVisible();

    await ensureHamburgerMenuOpen(page);

    // Navigate to About
    await page.getByRole('banner').getByRole('link', { name: /^About$/ }).first().click();
    await expect(page).toHaveURL(/\/about\/?$/);

    // Destination page loads successfully
    await expect(page).toHaveTitle(/About EPAM|\bAbout\b/i);

    // Global header remains available
    await expect(page.getByRole('banner')).toBeVisible();
    await expect(page.getByRole('banner').getByRole('link', { name: /^Careers$/ }).first()).toBeVisible();
  });

  test('Header remains usable after navigating to Careers from Insights', async ({ page }) => {
    await page.goto(INSIGHTS_URL, { waitUntil: 'domcontentloaded' });

    await ensureHamburgerMenuOpen(page);

    await page.getByRole('banner').getByRole('link', { name: /^Careers$/ }).first().click();
    await expect(page).toHaveURL(/\/careers\/?$/);
    await expect(page).toHaveTitle(/Careers/i);

    await expect(page.getByRole('banner')).toBeVisible();
    await expect(page.getByRole('banner').getByRole('link', { name: /^Insights$/ }).first()).toBeVisible();
  });

  test('Navigation items open in same tab (internal) and footer social opens in new tab (external indication)', async ({ page, context }) => {
    await page.goto(INSIGHTS_URL, { waitUntil: 'domcontentloaded' });

    // Internal header links should not have target=_blank
    const topNav = page.locator('header').getByRole('navigation', { name: 'Main navigation' }).first();
    await expect(topNav.getByRole('link', { name: /^About$/ }).first()).not.toHaveAttribute('target', '_blank');
    await expect(topNav.getByRole('link', { name: /^Careers$/ }).first()).not.toHaveAttribute('target', '_blank');

    // Footer social links are indicated with "(opens in a new tab)" and use target=_blank
    const footer = page.getByRole('contentinfo');
    await footer.scrollIntoViewIfNeeded();

    const linkedIn = footer.getByRole('link', { name: /LinkedIn .*opens in a new tab/i }).first();
    await expect(linkedIn).toHaveAttribute('target', '_blank');

    // Additionally verify new page is created when clicking
    const [newPage] = await Promise.all([
      context.waitForEvent('page'),
      linkedIn.click()
    ]);
    await newPage.waitForLoadState('domcontentloaded');
    await expect(newPage).toHaveURL(/linkedin\.com/);

    // Original tab remains on Insights
    await expect(page).toHaveURL(INSIGHTS_URL);

    await newPage.close();
  });

  test('Footer legal links (Privacy Policy, Cookie Policy) resolve and load successfully', async ({ page }) => {
    await page.goto(INSIGHTS_URL, { waitUntil: 'domcontentloaded' });

    const footer = page.getByRole('contentinfo');
    await footer.scrollIntoViewIfNeeded();

    const privacyHref = await footer.getByRole('link', { name: /privacy policy/i }).first().getAttribute('href');
    const cookieHref = await footer.getByRole('link', { name: /cookie policy/i }).first().getAttribute('href');

    expect(privacyHref).toContain('privacy');
    expect(cookieHref).toContain('cookie');

    // Navigate via hrefs to avoid site intercepts that can block the click in automation
    await page.goto(String(privacyHref), { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/privacy-policy/);
    await expect(page).toHaveTitle(/Privacy/i);

    await page.goto(INSIGHTS_URL, { waitUntil: 'domcontentloaded' });
    await footer.scrollIntoViewIfNeeded();
    await page.goto(String(cookieHref), { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/cookie-policy/);
    await expect(page).toHaveTitle(/Cookie/i);
  });
});
