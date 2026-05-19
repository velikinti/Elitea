import { test, expect } from '@playwright/test';

test.describe('Catalog browsing, search, PDP, and cart basics', () => {
  test('Category listing displays product tiles with name and price', async ({ page }) => {
    await page.goto('/books');

    const tiles = page.locator('.product-item');
    await expect(tiles.first()).toBeVisible();

    const first = tiles.first();
    await expect(first.locator('.product-title')).toBeVisible();
    await expect(first.locator('.prices')).toBeVisible();
  });

  test('Selecting a search result opens its product detail page', async ({ page }) => {
    await page.goto('/');

    await page.locator('#small-searchterms').fill('computer');
    await page.getByRole('button', { name: 'Search' }).click();
    await expect(page).toHaveURL(/\/search\?q=computer/);

    const firstResult = page.locator('.product-item').first();
    const name = await firstResult.locator('.product-title a').innerText();
    await firstResult.locator('.product-title a').click();

    await expect(page.locator('h1')).toContainText(name.trim());
    await expect(page.locator('.product-price')).toBeVisible();
    await expect(page.getByRole('button', { name: /add to cart/i }).first()).toBeVisible();
  });

  test('Add to cart from PDP shows notification and cart contains item', async ({ page }) => {
    // Use a stable product URL we observed during manual execution
    await page.goto('/build-your-cheap-own-computer');

    await expect(page.locator('h1')).toContainText('Build your own cheap computer');

    await page.getByRole('button', { name: /add to cart/i }).first().click();

    const bar = page.locator('#bar-notification');
    await expect(bar).toBeVisible();
    await expect(bar).toContainText('The product has been added to your shopping cart');

    await page.getByRole('link', { name: /shopping cart/i }).first().click();
    await expect(page).toHaveURL(/\/cart/);

    await expect(page.locator('.cart-item-row').first()).toBeVisible();
    await expect(page.locator('input.qty-input').first()).toHaveValue(/\d+/);
  });

  test('Empty cart shows empty message', async ({ page }) => {
    await page.goto('/cart');

    // Remove everything (if any) to reach an empty cart state
    const remove = page.locator('input[name^="removefromcart"]');
    const count = await remove.count();
    for (let i = 0; i < count; i++) {
      await remove.nth(i).check();
    }
    if (count > 0) {
      await page.getByRole('button', { name: /update shopping cart/i }).click();
    }

    await expect(page.locator('.order-summary-content')).toContainText(/empty/i);
  });
});
