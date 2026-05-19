import { test, expect } from '@playwright/test';

function expectCountGreaterThan(locator: ReturnType<any>, min: number) {
  return expect
    .poll(async () => locator.count(), { message: `Expected count to be > ${min}` })
    .toBeGreaterThan(min);
}

const isNonDecreasing = (arr: number[]) => arr.every((v, i) => i === 0 || arr[i - 1] <= v);
const isNonIncreasing = (arr: number[]) => arr.every((v, i) => i === 0 || arr[i - 1] >= v);

async function getListingNames(page: any): Promise<string[]> {
  return await page.locator('.product-item h2 a').allTextContents();
}

async function getListingPrices(page: any): Promise<number[]> {
  const texts = await page.locator('.product-item .prices .actual-price').allTextContents();
  return texts
    .map((t: string) => parseFloat(t.replace(/[^0-9.]/g, '')))
    .filter((n: number) => !Number.isNaN(n));
}

test.describe('Demo Web Shop - listing sorting/paging + compare + cart promotions + blog', () => {
  test('Sort control changes product order (Price: Low to High)', async ({ page }) => {
    await page.goto('/books');

    await expect(page.locator('#products-orderby')).toBeVisible();
    const before = await getListingPrices(page);
    expect(before.length).toBeGreaterThanOrEqual(2);

    await page.locator('#products-orderby').selectOption({ label: 'Price: Low to High' });
    await expect(page).toHaveURL(/orderby=10/);

    const after = await getListingPrices(page);
    expect(after.length).toBeGreaterThanOrEqual(2);
    expect(isNonDecreasing(after)).toBeTruthy();
  });

  test('Sort control changes product order (Name: A to Z)', async ({ page }) => {
    await page.goto('/books');

    await expect(page.locator('#products-orderby')).toBeVisible();
    const before = await getListingNames(page);
    expect(before.length).toBeGreaterThanOrEqual(2);

    await page.locator('#products-orderby').selectOption({ label: 'Name: A to Z' });
    await expect(page).toHaveURL(/orderby=5/);

    const after = await getListingNames(page);
    expect(after.length).toBeGreaterThanOrEqual(2);
    const sorted = [...after].sort((a, b) => a.localeCompare(b));
    expect(after).toEqual(sorted);
  });

  test('Applied sort remains when navigating to another results page (Price: High to Low)', async ({ page }) => {
    // Use books + pagesize=4 to ensure paging exists.
    await page.goto('/books?pagesize=4');
    await page.locator('#products-orderby').selectOption({ label: 'Price: High to Low' });
    await expect(page).toHaveURL(/orderby=11/);

    await page.getByRole('link', { name: '2', exact: true }).click();
    await expect(page).toHaveURL(/pagenumber=2/);

    const selected = (await page.locator('#products-orderby option:checked').textContent())?.trim();
    expect(selected).toBe('Price: High to Low');

    const prices = await getListingPrices(page);
    expect(prices.length).toBeGreaterThanOrEqual(1);
    expect(isNonIncreasing(prices)).toBeTruthy();
  });

  test('Unsupported sort parameter in URL falls back to default sorting', async ({ page }) => {
    await page.goto('/books?orderby=9999');
    await expect(page.locator('#products-orderby')).toBeVisible();
    const selectedText = (await page.locator('#products-orderby option:checked').textContent())?.trim();
    expect(selectedText).toBe('Position');

    
  });

  test('Change page size updates the number of products shown (pagesize=4)', async ({ page }) => {
    await page.goto('/books');
    await page.locator('#products-pagesize').selectOption({ label: '4' });
    await expect(page).toHaveURL(/pagesize=4/);

    await expect(page.locator('.product-item')).toHaveCount(4);
  });

  test('Navigate using a page number shows that page', async ({ page }) => {
    await page.goto('/books?pagesize=4');
    await page.getByRole('link', { name: '2', exact: true }).click();
    await expect(page).toHaveURL(/pagenumber=2/);
    await expectCountGreaterThan(page.locator('.product-item'), 0);
  });

  test('Compare products list: add 2 items, verify, then clear shows empty state', async ({ page }) => {
    // Add first product
    await page.goto('/computing-and-internet');
    await page.getByRole('button', { name: 'Add to compare list' }).click();
    await expect(page).toHaveURL(/\/compareproducts/);

    // Add second product
    await page.goto('/science');
    await page.getByRole('button', { name: 'Add to compare list' }).click();
    await expect(page).toHaveURL(/\/compareproducts/);

    const compared = page.locator('table.compare-products-table tr.product-name td a');
    await expect(compared).toHaveCount(2);

    await page.getByRole('link', { name: 'Clear list' }).click();
    await expect(page.getByText('You have no items to compare.')).toBeVisible();
    await expect(page.locator('table.compare-products-table')).toHaveCount(0);
  });

  test('Recently viewed products page shows visited products (most recent first)', async ({ page }) => {
    // Visit A, B, C in order
    await page.goto('/build-your-own-computer');
    await page.goto('/computing-and-internet');
    await page.goto('/science');

    await page.goto('/recentlyviewedproducts');
    const names = page.locator('.product-item h2 a');
    await expect(names.first()).toHaveText('Science');
  });

  test('Cart promotions: invalid discount code shows error, and terms-of-service blocks checkout if unchecked', async ({ page }) => {
    // Ensure we have an item in cart (use add-to-cart from PDP)
    await page.goto('/computing-and-internet');
    await page.getByRole('button', { name: 'Add to cart' }).click();
    await page.goto('/cart');

    // Invalid coupon
    await page.locator('input[name="discountcouponcode"]').fill('INVALIDCODE');
    await page.locator('input[name="applydiscountcouponcode"]').click();
    await expect(page.getByText("The coupon code you entered couldn't be applied to your order")).toBeVisible();

    // Checkout blocked by ToS when unchecked
    await expect(page.locator('#termsofservice')).toBeVisible();
    await page.locator('#termsofservice').uncheck();
    await page.getByRole('button', { name: 'Checkout' }).click();
    await expect(page.locator('#terms-of-service-warning-box')).toContainText('Please accept the terms of service');
  });

  test('Blog listing shows posts and blog detail page shows content', async ({ page }) => {
    await page.goto('/blog');
    await expectCountGreaterThan(page.locator('.post'), 0);

    // Navigate directly to a known post from listing content we observed.
    await page.goto('/customer-service-client-service');
    await expect(page.locator('.page-title h1')).toContainText('Customer Service - Client Service');
    await expect(page.locator('.page-body')).toBeVisible();
  });
});
