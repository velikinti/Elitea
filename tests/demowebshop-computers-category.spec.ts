import { test, expect } from '@playwright/test';

test.describe('Demo Web Shop - Computers category & related UX', () => {
  test('Computers category landing renders and contains subcategories', async ({ page }) => {
    await page.goto('/computers');

    await expect(page.getByRole('heading', { name: 'Computers', level: 1 })).toBeVisible();

    // Subcategory tiles exist on this landing page.
    await expect(page.getByRole('link', { name: 'Desktops' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Notebooks' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Accessories' })).toBeVisible();

    // Critical sections present (header navigation + breadcrumbs)
    await expect(page.getByRole('link', { name: 'Tricentis Demo Web Shop' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Home' })).toBeVisible();
  });

  test('Header navigation: Electronics link redirects to Electronics category', async ({ page }) => {
    await page.goto('/computers');

    await expect(page.getByRole('link', { name: 'Electronics' }).first()).toBeVisible();
    await page.getByRole('link', { name: 'Electronics' }).first().click();

    await expect(page).toHaveURL(/\/electronics/);
    await expect(page.getByRole('heading', { name: 'Electronics', level: 1 })).toBeVisible();
  });

  test('Header search: searching for "notebook" navigates to search and shows a results/empty-state message', async ({ page }) => {
    await page.goto('/computers');

    const search = page.getByRole('textbox', { name: 'Search store' });
    await expect(search).toBeVisible();

    await search.fill('notebook');
    await page.getByRole('button', { name: 'Search' }).click();

    await expect(page).toHaveURL(/\/search\?q=notebook/);

    // Demo site may return products or an empty-state; validate it's not broken.
    const noProducts = page.getByText('No products were found that matched your criteria.');
    const resultsGrid = page.locator('.product-grid');
    await expect(noProducts.or(resultsGrid)).toBeVisible();
  });

  test('Breadcrumbs: Home breadcrumb navigates to homepage', async ({ page }) => {
    await page.goto('/computers');

    await expect(page.getByRole('link', { name: 'Home' })).toBeVisible();
    await page.getByRole('link', { name: 'Home' }).click();

    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole('heading', { name: 'Welcome to our store', level: 2 })).toBeVisible();
  });

  test('Subcategory: open Desktops and verify listing controls work (sort, page size, view mode)', async ({ page }) => {
    await page.goto('/computers');
    await page.getByRole('link', { name: 'Desktops' }).first().click();

    await expect(page).toHaveURL(/\/desktops/);
    await expect(page.getByRole('heading', { name: 'Desktops', level: 1 })).toBeVisible();

    // Listing controls exist on Desktops.
    await expect(page.locator('#products-orderby')).toBeVisible();
    await expect(page.locator('#products-pagesize')).toBeVisible();
    await expect(page.locator('#products-viewmode')).toBeVisible();

    // Sort: Price low to high results in non-decreasing displayed prices.
    await page.locator('#products-orderby').selectOption({ label: 'Price: Low to High' });
    const prices = page.locator('.product-item .prices');
    await expect(prices.first()).toBeVisible();

    const priceNums = (await prices.allTextContents())
      .map((t) => (t.match(/[0-9]+(\.[0-9]+)?/) || [null])[0])
      .filter((v): v is string => !!v)
      .map((v) => Number(v));

    const sorted = [...priceNums].sort((a, b) => a - b);
    expect(priceNums, 'Prices should be sorted ascending').toEqual(sorted);

    // Page size: set to 12; product count should be <= 12.
    await page.locator('#products-pagesize').selectOption({ label: '12' });
    await expect(page.locator('.product-item').first()).toBeVisible();
    const productCount = await page.locator('.product-item').count();
    expect(productCount).toBeLessThanOrEqual(12);

    // View mode: set to List and verify list layout is present.
    await page.locator('#products-viewmode').selectOption({ label: 'List' });
    await expect(page.locator('.product-list')).toBeVisible();
  });

  test('"New tab" subcategory destination (substitution): Notebooks destination loads correctly', async ({ page }) => {
    // Substitution: in test we open in a new tab via browser context to simulate new-tab.
    await page.goto('/computers');

    const [newTab] = await Promise.all([
      page.context().waitForEvent('page'),
      page.evaluate(() => window.open('/notebooks', '_blank')),
    ]);

    await newTab.waitForLoadState('domcontentloaded');
    await expect(newTab).toHaveURL(/\/notebooks/);
    await expect(newTab.getByRole('heading', { name: 'Notebooks', level: 1 })).toBeVisible();
    await newTab.close();
  });
});
