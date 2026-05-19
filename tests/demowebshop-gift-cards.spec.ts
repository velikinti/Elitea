import { test, expect } from '@playwright/test';

const GIFT_CARDS_PATH = '/gift-cards';

test.describe('Gift Cards category page - header, search, sorting, view mode, cart validation (Demo Web Shop)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(GIFT_CARDS_PATH);
    await expect(page).toHaveURL(new RegExp(`${GIFT_CARDS_PATH.replace('/', '\\/')}`));
    await expect(page.getByRole('heading', { name: 'Gift Cards' })).toBeVisible();
  });

  test('Header navigation links are visible and clickable (top menu)', async ({ page }) => {
    const topMenu = page.locator('ul.top-menu');
    await expect(topMenu).toBeVisible();

    const links = topMenu.getByRole('link');
    await expect(links.first()).toBeVisible();

    // Click a category link and ensure navigation works.
    await links.first().click();
    await expect(page).not.toHaveURL(new RegExp(`${GIFT_CARDS_PATH.replace('/', '\\/')}`));
  });

  test('Shopping cart entry point from header opens cart page', async ({ page }) => {
    await page.getByRole('link', { name: /Shopping cart/i }).click();
    await expect(page).toHaveURL(/\/cart/);
    await expect(page.getByRole('heading', { name: /Shopping cart/i })).toBeVisible();
  });

  test('Wishlist entry point from header opens wishlist page', async ({ page }) => {
    await page.getByRole('link', { name: /Wishlist/i }).click();
    await expect(page).toHaveURL(/\/wishlist/);
    await expect(page.getByRole('heading', { name: /Wishlist/i })).toBeVisible();
  });

  test('Global search with a valid term navigates to results', async ({ page }) => {
    await page.locator('#small-searchterms').fill('gift');
    await page.getByRole('button', { name: 'Search' }).click();

    await expect(page).toHaveURL(/\/search\?q=gift/);

    // Either results exist, or an empty-state message appears.
    const emptyMessage = page.getByText('No products were found that matched your criteria.');
    const results = page.locator('.product-grid, .product-list');
    await expect(emptyMessage.or(results)).toBeVisible();
  });

  test('Global search shows empty-results message for non-existent term', async ({ page }) => {
    await page.locator('#small-searchterms').fill('zzzz_nonexistent_product_12345');
    await page.getByRole('button', { name: 'Search' }).click();

    await expect(page).toHaveURL(/\/search\?q=zzzz_nonexistent_product_12345/);
    await expect(page.getByText('No products were found that matched your criteria.')).toBeVisible();
  });

  test('Submitting empty search shows validation dialog and stays on current page', async ({ page }) => {
    page.on('dialog', async (dialog) => {
      expect(dialog.type()).toBe('alert');
      expect(dialog.message()).toMatch(/Please enter some search keyword/i);
      await dialog.accept();
    });

    await page.locator('#small-searchterms').fill('');
    await page.getByRole('button', { name: 'Search' }).click();

    await expect(page).toHaveURL(new RegExp(`${GIFT_CARDS_PATH.replace('/', '\\/')}`));
  });

  test('Search with special characters is handled gracefully (no crash)', async ({ page }) => {
    await page.locator('#small-searchterms').fill('!@#$%^&*()_+[]{};\':",.<>/?');
    await page.getByRole('button', { name: 'Search' }).click();

    await expect(page).toHaveURL(/\/search\?q=/);
    await expect(page.getByRole('heading', { name: 'Search' })).toBeVisible();

    const emptyMessage = page.getByText('No products were found that matched your criteria.');
    const results = page.locator('.product-grid, .product-list');
    await expect(emptyMessage.or(results)).toBeVisible();
  });

  test('Very long search input is handled within limits (no crash)', async ({ page }) => {
    const longTerm = 'x'.repeat(200);
    await page.locator('#small-searchterms').fill(longTerm);
    await page.getByRole('button', { name: 'Search' }).click();

    await expect(page).toHaveURL(/\/search\?q=/);
    await expect(page.getByRole('heading', { name: 'Search' })).toBeVisible();
  });

  test('Gift Cards PLP shows product tiles with name, price and clickable title/image', async ({ page }) => {
    const firstProduct = page.locator('.item-box').first();
    await expect(firstProduct).toBeVisible();

    const titleLink = firstProduct.locator('h2.product-title a');
    const imgLink = firstProduct.locator('.product-item .picture a');
    const price = firstProduct.locator('.prices .actual-price');

    await expect(titleLink).toBeVisible();
    await expect(imgLink).toBeVisible();
    await expect(price).toBeVisible();

    const productName = (await titleLink.textContent())?.trim() ?? '';
    await titleLink.click();
    await expect(page.getByRole('heading', { name: productName })).toBeVisible();

    await page.goBack();
    await expect(page).toHaveURL(new RegExp(`${GIFT_CARDS_PATH.replace('/', '\\/')}`));

    await imgLink.click();
    await expect(page).not.toHaveURL(new RegExp(`${GIFT_CARDS_PATH.replace('/', '\\/')}`));
  });

  test('Sort and view mode controls are visible and can be changed', async ({ page }) => {
    await expect(page.locator('#products-orderby')).toBeVisible();
    await expect(page.locator('#products-viewmode')).toBeVisible();

    await page.locator('#products-orderby').selectOption({ label: 'Price: Low to High' });
    await expect(page).toHaveURL(/orderby=10/);

    await page.locator('#products-viewmode').selectOption({ label: 'List' });
    await expect(page).toHaveURL(/viewmode=list/);
    await expect(page.locator('#products-viewmode')).toHaveValue('list');
  });

  test('Add to cart from PLP redirects to PDP when required fields exist; attempting add without fields shows validation', async ({ page }) => {
    // On Gift Cards, Add to cart from listing takes you to PDP (gift cards require recipient/sender info).
    await page.locator('.item-box').first().getByRole('button', { name: 'Add to cart' }).click();
    await expect(page).toHaveURL(/\/\d+-virtual-gift-card|\/\d+-physical-gift-card|\/5-virtual-gift-card|\/25-virtual-gift-card|\/50-physical-gift-card|\/100-physical-gift-card/);

    await page.locator('input[id^="add-to-cart-button-"]').click();

    // Validation appears in a notification area.
    await expect(page.getByText(/Enter valid recipient name/i)).toBeVisible();
    await expect(page.getByText(/Enter valid recipient email/i)).toBeVisible();
  });

  test.describe('Responsiveness smoke (header + products visible)', () => {
    const viewports = [
      { name: 'desktop 1280x800', width: 1280, height: 800 },
      { name: 'tablet 768x1024', width: 768, height: 1024 },
      { name: 'mobile 375x667', width: 375, height: 667 },
    ];

    for (const vp of viewports) {
      test(`Gift Cards page remains usable on ${vp.name}`, async ({ page }) => {
        await page.setViewportSize({ width: vp.width, height: vp.height });
        await page.goto(GIFT_CARDS_PATH);

        await expect(page.locator('#small-searchterms')).toBeVisible();
        await expect(page.locator('.header-links')).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Gift Cards' })).toBeVisible();

        // At least one product tile should be visible for this demo site.
        await expect(page.locator('.item-box').first()).toBeVisible();
      });
    }
  });

  test('Performance: Gift Cards main content becomes visible within budget', async ({ page }) => {
    const start = Date.now();
    await page.goto(GIFT_CARDS_PATH);

    await expect(page.getByRole('heading', { name: 'Gift Cards' })).toBeVisible();
    await expect(page.locator('.item-box').first()).toBeVisible();

    const elapsedMs = Date.now() - start;
    expect(elapsedMs).toBeLessThan(10_000);
  });
});
