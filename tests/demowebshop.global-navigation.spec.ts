import { test, expect, Page } from '@playwright/test';

async function registerAndLogin(page: Page) {
  const uniqueEmail = `pw_${Date.now()}@example.com`;
  const password = 'Password123!';

  await page.goto('/register');
  // Gender is optional for our purposes; check if present
  const female = page.locator('#gender-female');
  if (await female.count()) await female.check();

  await page.locator('#FirstName').fill('Play');
  await page.locator('#LastName').fill('Wright');
  await page.locator('#Email').fill(uniqueEmail);
  await page.locator('#Password').fill(password);
  await page.locator('#ConfirmPassword').fill(password);
  await page.getByRole('button', { name: 'Register' }).click();

  await expect(page.locator('.result')).toContainText('Your registration completed');
  await expect(page.getByRole('link', { name: 'Log out' })).toBeVisible();

  return { email: uniqueEmail, password };
}

test.describe('Global navigation across the site (header, menu)', () => {
  test('Navigate to Books category from top menu', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'Books' }).first().click();
    await expect(page).toHaveURL(/\/books/);
    await expect(page.getByRole('heading', { name: 'Books' })).toBeVisible();
  });

  test('Header shows Search/Cart/Wishlist/Login/Register when signed out', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('#small-searchterms')).toBeVisible();
    await expect(page.getByRole('link', { name: /shopping cart/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /wishlist/i })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Log in' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Register' })).toBeVisible();

    await expect(page.getByRole('link', { name: 'My account' })).toHaveCount(0);
    await expect(page.getByRole('link', { name: 'Log out' })).toHaveCount(0);
  });

  test('Header shows My account and Log out when signed in', async ({ page }) => {
    await registerAndLogin(page);

    // The demo site shows email in header instead of literal "My account".
    await expect(page.getByRole('link', { name: 'Log out' })).toBeVisible();
    await expect(page.getByRole('link', { name: /@example\.com/ })).toBeVisible();

    await expect(page.getByRole('link', { name: 'Log in' })).toHaveCount(0);
    await expect(page.getByRole('link', { name: 'Register' })).toHaveCount(0);
  });

  test('Top menu categories are keyboard accessible (Books via Enter)', async ({ page }) => {
    await page.goto('/');

    // Focus the Books link and activate via Enter
    const books = page.getByRole('link', { name: 'Books' }).first();
    await books.focus();
    await page.keyboard.press('Enter');

    await expect(page).toHaveURL(/\/books/);
    await expect(page.getByRole('heading', { name: 'Books' })).toBeVisible();
  });
});
