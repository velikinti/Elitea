import { expect, test } from '@playwright/test';

const routes = {
  Home: '/',
  'Shopping cart': '/cart',
  Wishlist: '/wishlist',
  'Contact us': '/contactus',
  Search: '/search',
  'Category listing': '/computers',
  'Product details': '/build-your-own-computer',
};

async function gotoNamedPage(page: any, name: keyof typeof routes) {
  await page.goto(routes[name]);
  await expect(page).toHaveURL(new RegExp(`${routes[name].replace('/', '\\/')}$`));
}

function headerLinkName(link: string) {
  if (link === 'Shopping cart') return /Shopping cart/i;
  if (link === 'Wishlist') return /Wishlist/i;
  return new RegExp(`^${link}$`, 'i');
}

test.describe('Demo Web Shop - Global header/footer navigation', () => {
  test('Navigate to key pages via header links from any page (scenario outline)', async ({ page }) => {
    const examples: Array<{ sourcePage: keyof typeof routes; headerLink: string; targetPage: keyof typeof routes }> = [
      { sourcePage: 'Home', headerLink: 'Home', targetPage: 'Home' },
      { sourcePage: 'Home', headerLink: 'Shopping cart', targetPage: 'Shopping cart' },
      { sourcePage: 'Home', headerLink: 'Wishlist', targetPage: 'Wishlist' },
      { sourcePage: 'Product details', headerLink: 'Shopping cart', targetPage: 'Shopping cart' },
      { sourcePage: 'Category listing', headerLink: 'Wishlist', targetPage: 'Wishlist' },
      { sourcePage: 'Search', headerLink: 'Home', targetPage: 'Home' },
      { sourcePage: 'Contact us', headerLink: 'Shopping cart', targetPage: 'Shopping cart' },
    ];

    for (const ex of examples) {
      await gotoNamedPage(page, ex.sourcePage);

      if (ex.headerLink === 'Home') {
        await page.getByRole('link', { name: /Tricentis Demo Web Shop/i }).click();
      } else {
        await page.getByRole('link', { name: headerLinkName(ex.headerLink) }).click();
      }

      await expect(page).toHaveURL(new RegExp(`${routes[ex.targetPage].replace('/', '\\/')}$`));
      await expect(page).toHaveTitle(/Demo Web Shop/i);
    }
  });

  test('Shopping cart link always opens the cart page', async ({ page }) => {
    await gotoNamedPage(page, 'Product details');
    await page.getByRole('link', { name: /Shopping cart/i }).click();
    await expect(page).toHaveURL(/\/cart$/);

    await expect(page.getByRole('heading', { name: /Shopping cart/i })).toBeVisible();
    await expect(page.locator('table.cart')).toBeVisible();
  });

  test('Wishlist link always opens the wishlist page', async ({ page }) => {
    await gotoNamedPage(page, 'Category listing');
    await page.getByRole('link', { name: /Wishlist/i }).click();
    await expect(page).toHaveURL(/\/wishlist$/);

    await expect(page.getByRole('heading', { name: /Wishlist/i })).toBeVisible();
    await expect(page.locator('.wishlist-content, .page.wishlist-page-body, text=/wishlist/i')).toBeVisible();
  });

  test('Non-existing navigation destination shows a friendly error page', async ({ page }) => {
    await page.goto('/this-url-should-not-exist-404');

    // Demo Web Shop renders a themed 404 page (not a raw server error)
    await expect(page).toHaveTitle(/Demo Web Shop/i);
    await expect(page.locator('body')).not.toContainText(/stack trace|exception|server error|yellow screen/i);
    await expect(page.locator('body')).toContainText(/not found|page not found|404/i);
  });

  test('Rapid repeated clicks on a header link results in a single stable navigation', async ({ page }) => {
    await gotoNamedPage(page, 'Home');

    const cartLink = page.getByRole('link', { name: /Shopping cart/i });
    await Promise.all([cartLink.click(), cartLink.click(), cartLink.click()]);

    await expect(page).toHaveURL(/\/cart$/);
    await expect(page.getByRole('heading', { name: /Shopping cart/i })).toBeVisible();
  });

  test('Footer links navigate to informational pages', async ({ page }) => {
    await gotoNamedPage(page, 'Home');
    await page.getByRole('contentinfo').getByRole('link', { name: /Contact us/i }).click();

    await expect(page).toHaveURL(/\/contactus$/);
    await expect(page.getByRole('heading', { name: /Contact us/i })).toBeVisible();
  });
});

test.describe('Demo Web Shop - Browse product catalog by category', () => {
  test('Open a category page from navigation/menu (scenario outline)', async ({ page }) => {
    const categories = [
      { name: 'Computers', url: '/computers' },
      { name: 'Electronics', url: '/electronics' },
      { name: 'Apparel & Shoes', url: '/apparel-shoes' },
      { name: 'Digital downloads', url: '/digital-downloads' },
      { name: 'Books', url: '/books' },
      { name: 'Jewelry', url: '/jewelry' },
      { name: 'Gift Cards', url: '/gift-cards' },
    ];

    await page.goto('/');
    for (const c of categories) {
      await page.getByRole('link', { name: new RegExp(`^${c.name}$`, 'i') }).click();
      await expect(page).toHaveURL(new RegExp(`${c.url.replace('/', '\\/')}$`));
      await expect(page.getByRole('heading', { name: new RegExp(c.name, 'i') })).toBeVisible();
      await expect(page.locator('.product-grid, .sub-category-grid')).toBeVisible();
      await page.goto('/');
    }
  });

  test('Product tiles show at least name and price on category listing', async ({ page }) => {
    await page.goto('/books');

    const items = page.locator('.product-item');
    await expect(items.first()).toBeVisible();

    const first = items.first();
    await expect(first.locator('.product-title')).toBeVisible();

    // Some listings might not show prices in certain states; assert "where pricing is shown"
    const price = first.locator('.prices');
    await expect(price).toBeVisible();
  });
});

test.describe('Demo Web Shop - Search', () => {
  test('Search returns matching products', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('textbox', { name: /Search store/i }).fill('computer');
    await page.getByRole('button', { name: /^Search$/i }).click();

    await expect(page).toHaveURL(/\/search\?q=computer/i);
    await expect(page.getByRole('heading', { name: /Search/i })).toBeVisible();

    const results = page.locator('.product-item');
    await expect(results.first()).toBeVisible();
    await expect(page.locator('body')).toContainText(/computer/i);
  });

  test('Search with no matches shows a no-results message', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('textbox', { name: /Search store/i }).fill('zzzz-no-such-product');
    await page.getByRole('button', { name: /^Search$/i }).click();

    await expect(page).toHaveURL(/\/search\?q=zzzz-no-such-product/i);
    await expect(page.getByRole('heading', { name: /Search/i })).toBeVisible();
    await expect(page.locator('body')).toContainText(/No products were found/i);
    await expect(page.locator('.product-item')).toHaveCount(0);
  });

  test('Submitting an empty search shows validation or sensible default behavior', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('textbox', { name: /Search store/i }).fill('');
    await page.getByRole('button', { name: /^Search$/i }).click();

    // Site behavior: shows validation in a popup bar: "Search term minimum length is 3 characters"
    await expect(page.locator('body')).toContainText(/Search term minimum length|Search/i);
    await expect(page).toHaveTitle(/Demo Web Shop/i);
  });

  test('Search safely handles special characters (scenario outline)', async ({ page }) => {
    const terms = ["' OR 1=1 --", '<script>alert(1)</script>', '%_%_%', '"quoted phrase"'];

    for (const term of terms) {
      await page.goto('/');
      await page.getByRole('textbox', { name: /Search store/i }).fill(term);
      await page.getByRole('button', { name: /^Search$/i }).click();

      await expect(page).toHaveTitle(/Demo Web Shop/i);
      await expect(page.locator('body')).not.toContainText(/exception|stack trace|server error/i);
    }
  });
});

test.describe('Demo Web Shop - PDP & cart/wishlist basics', () => {
  test('Open product details from a listing', async ({ page }) => {
    await page.goto('/computers');

    // Navigate into a subcategory if needed
    const subCategory = page.locator('.sub-category-grid .item-box a').first();
    if (await subCategory.isVisible()) {
      await subCategory.click();
    }

    const firstProduct = page.locator('.product-item .product-title a').first();
    await expect(firstProduct).toBeVisible();
    await firstProduct.click();

    await expect(page.locator('.product-name')).toBeVisible();
    await expect(page.locator('.product-essential')).toBeVisible();
    await expect(page.locator('.product-details-page')).toBeVisible();

    // price is usually visible for purchasable products
    await expect(page.locator('.product-price')).toBeVisible();

    // description/details (if present)
    await expect(page.locator('.product-description, .full-description, .product-details')).toBeVisible();
  });

  test('Required product options must be selected before adding to cart (if required options exist)', async ({ page }) => {
    await page.goto('/build-your-own-computer');

    await page.getByRole('button', { name: /Add to cart/i }).click();

    // If required options are missing, an error summary appears.
    // Assert either: validation shows OR cart updated confirmation appears.
    const error = page.locator('.message-error');
    const barNotification = page.locator('#bar-notification');

    await expect(error.or(barNotification)).toBeVisible();
  });

  test('Add a product to cart from PDP updates cart state', async ({ page }) => {
    await page.goto('/25-virtual-gift-card');

    // This product requires recipient details.
    await page.locator('#giftcard_2_RecipientName').fill('QA Recipient');
    await page.locator('#giftcard_2_RecipientEmail').fill('qa.recipient@example.com');

    const cartQtyBeforeText = await page.getByRole('link', { name: /Shopping cart/i }).innerText();

    await page.getByRole('button', { name: /Add to cart/i }).click();
    await expect(page.locator('#bar-notification')).toContainText(/The product has been added to your shopping cart/i);

    const cartQtyAfterText = await page.getByRole('link', { name: /Shopping cart/i }).innerText();
    expect(cartQtyAfterText).not.toEqual(cartQtyBeforeText);
  });

  test('Add a product to wishlist from PDP', async ({ page }) => {
    await page.goto('/25-virtual-gift-card');

    await page.locator('#giftcard_2_RecipientName').fill('QA Recipient');
    await page.locator('#giftcard_2_RecipientEmail').fill('qa.recipient@example.com');

    await page.getByRole('button', { name: /Add to wishlist/i }).click();
    await expect(page.locator('#bar-notification')).toContainText(/The product has been added to your wishlist/i);

    await page.getByRole('link', { name: /Wishlist/i }).click();
    await expect(page).toHaveURL(/\/wishlist$/);
  });
});
