import { test, expect } from '@playwright/test';

function toNumber(text: string): number | null {
  const m = text.match(/[0-9]+(\.[0-9]+)?/);
  return m ? Number(m[0]) : null;
}

test.describe('Demo Web Shop - Gift Cards', () => {
  test('Gift Cards category shows heading and product grid/list', async ({ page }) => {
    await page.goto('/gift-cards');

    await expect(page.getByRole('heading', { name: 'Gift Cards', level: 1 })).toBeVisible();

    // Critical sections
    await expect(page.getByRole('link', { name: 'Tricentis Demo Web Shop' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Home' })).toBeVisible();

    // Products grid or empty-state
    const listing = page.locator('.product-grid, .product-list');
    const emptyState = page.getByText('No products were found that matched your criteria.');
    await expect(listing.or(emptyState)).toBeVisible();
  });

  test('Breadcrumb Home navigates to homepage', async ({ page }) => {
    await page.goto('/gift-cards');

    await page.getByRole('link', { name: 'Home' }).click();
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole('heading', { name: 'Welcome to our store' })).toBeVisible();
  });

  test('Open gift card details by clicking first product name', async ({ page }) => {
    await page.goto('/gift-cards');

    const first = page.locator('.product-item').first();
    await expect(first).toBeVisible();

    const name = (await first.locator('h2.product-title').innerText()).trim();
    await first.getByRole('link', { name, exact: true }).click();

    await expect(page.getByRole('heading', { name, level: 1 })).toBeVisible();
  });

  test('Open gift card details by clicking first product image', async ({ page }) => {
    await page.goto('/gift-cards');

    const first = page.locator('.product-item').first();
    await expect(first).toBeVisible();

    const name = (await first.locator('h2.product-title').innerText()).trim();
    // Image link has accessible name like "Picture of ..."
    await first.getByRole('link').first().click();

    await expect(page.getByRole('heading', { name, level: 1 })).toBeVisible();
  });

  test('Listing: Sort Price Low to High updates order (if control exists)', async ({ page }) => {
    await page.goto('/gift-cards');

    const sort = page.locator('#products-orderby');
    await expect(sort).toBeVisible();

    await sort.selectOption({ label: 'Price: Low to High' });

    const nums = (await page.locator('.product-item .prices').allTextContents())
      .map((t) => toNumber(t))
      .filter((v): v is number => v !== null);

    const sorted = [...nums].sort((a, b) => a - b);
    expect(nums).toEqual(sorted);
  });

  test('Invalid sort parameter in URL still loads successfully', async ({ page }) => {
    await page.goto('/gift-cards?orderby=INVALID');
    await expect(page.getByRole('heading', { name: 'Gift Cards', level: 1 })).toBeVisible();
    await expect(page.locator('.product-item').first()).toBeVisible();
  });

  test('Gift card PDP: clicking Add to cart with missing required fields shows validation and does not add', async ({ page }) => {
    await page.goto('/5-virtual-gift-card');

    // Capture cart qty before
    const before = await page
      .getByRole('link', { name: /Shopping cart \(\d+\)/ })
      .innerText();
    const beforeQty = Number((before.match(/\((\d+)\)/) || [null, '0'])[1]);

    await page.locator('#add-to-cart-button-1').click();

    // Validation appears in a popup bar.
    await expect(page.getByText('Enter valid recipient name')).toBeVisible();
    await expect(page.getByText('Enter valid recipient email')).toBeVisible();

    const after = await page
      .getByRole('link', { name: /Shopping cart \(\d+\)/ })
      .innerText();
    const afterQty = Number((after.match(/\((\d+)\)/) || [null, '0'])[1]);

    expect(afterQty).toBe(beforeQty);
  });

  test('Gift card PDP: spaces-only in required fields are treated as empty', async ({ page }) => {
    await page.goto('/5-virtual-gift-card');

    await page.getByRole('textbox', { name: "Recipient's Name:" }).fill('   ');
    await page.getByRole('textbox', { name: "Recipient's Email:" }).fill('   ');
    await page.getByRole('textbox', { name: 'Your Name:' }).fill('   ');
    await page.getByRole('textbox', { name: 'Your Email:' }).fill('   ');

    await page.locator('#add-to-cart-button-1').click();

    await expect(page.getByText('Enter valid recipient name')).toBeVisible();
    await expect(page.getByText('Enter valid sender email')).toBeVisible();
  });

  test('Gift card PDP: invalid recipient email blocks add-to-cart', async ({ page }) => {
    await page.goto('/5-virtual-gift-card');

    await page.getByRole('textbox', { name: "Recipient's Name:" }).fill('Alex Recipient');
    await page.getByRole('textbox', { name: "Recipient's Email:" }).fill('not-an-email');
    await page.getByRole('textbox', { name: 'Your Name:' }).fill('Sam Sender');
    await page.getByRole('textbox', { name: 'Your Email:' }).fill('sam@example.com');

    await page.locator('#add-to-cart-button-1').click();

    await expect(page.getByText('Enter valid recipient email')).toBeVisible();
  });

  test('Gift card PDP: fill required fields then Add to cart succeeds and item appears in cart', async ({ page }) => {
    await page.goto('/5-virtual-gift-card');

    await page.getByRole('textbox', { name: "Recipient's Name:" }).fill('Alex Recipient');
    await page.getByRole('textbox', { name: "Recipient's Email:" }).fill('alex@example.com');
    await page.getByRole('textbox', { name: 'Your Name:' }).fill('Sam Sender');
    await page.getByRole('textbox', { name: 'Your Email:' }).fill('sam@example.com');
    await page.getByRole('textbox', { name: 'Message:' }).fill('Happy birthday!');

    await page.locator('#add-to-cart-button-1').click();

    // Cart qty updates to at least 1
    await expect(page.getByRole('link', { name: /Shopping cart \(\d+\)/ })).toContainText('(1)');

    await page.getByRole('link', { name: /Shopping cart \(\d+\)/ }).click();

    await expect(page.getByRole('heading', { name: 'Shopping cart' })).toBeVisible();
    await expect(page.getByRole('link', { name: '$5 Virtual Gift Card' })).toBeVisible();

    // Verify configured details are present in the line item.
    await expect(page.getByText('From: Sam Sender')).toBeVisible();
    await expect(page.getByText('For: Alex Recipient')).toBeVisible();
  });

  test('Browser back after redirect (listing add-to-cart opens PDP) returns to Gift Cards listing', async ({ page }) => {
    await page.goto('/gift-cards');

    // For virtual gift cards, "Add to cart" from listing redirects to PDP to fill required fields.
    await page.locator('.product-item').first().getByRole('button', { name: 'Add to cart' }).click();
    await expect(page).toHaveURL(/\/\d+-virtual-gift-card/);

    await page.goBack();
    await expect(page).toHaveURL(/\/gift-cards/);
    await expect(page.getByRole('heading', { name: 'Gift Cards', level: 1 })).toBeVisible();
  });

  test('Accessibility (basic): tabbing reaches interactive elements and shows focus indicator', async ({ page }) => {
    await page.goto('/gift-cards');

    // Move focus a few steps; validate focused element has outline/boxShadow.
    for (let i = 0; i < 3; i++) await page.keyboard.press('Tab');

    const focusInfo = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el) return null;
      const cs = window.getComputedStyle(el);
      return {
        tag: el.tagName,
        text: (el.textContent || '').trim().slice(0, 80),
        outlineStyle: cs.outlineStyle,
        outlineWidth: cs.outlineWidth,
        boxShadow: cs.boxShadow,
      };
    });

    expect(focusInfo).not.toBeNull();
    expect(
      (focusInfo!.outlineStyle && focusInfo!.outlineStyle !== 'none') ||
        (focusInfo!.boxShadow && focusInfo!.boxShadow !== 'none'),
      'Focused element should have a visible focus indicator',
    ).toBeTruthy();
  });

  test('Performance: category and PDP load within threshold', async ({ page }) => {
    const thresholdMs = 5000;

    const t1 = Date.now();
    await page.goto('/gift-cards', { waitUntil: 'domcontentloaded' });
    const catMs = Date.now() - t1;
    expect(catMs).toBeLessThan(thresholdMs);

    const t2 = Date.now();
    await page.goto('/5-virtual-gift-card', { waitUntil: 'domcontentloaded' });
    const pdpMs = Date.now() - t2;
    expect(pdpMs).toBeLessThan(thresholdMs);
  });
});
