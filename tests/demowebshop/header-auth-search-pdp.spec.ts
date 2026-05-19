import { test, expect } from '@playwright/test';

const BASE = 'https://demowebshop.tricentis.com';

function uniqueEmail(prefix = 'new.user') {
  return `${prefix}+${Date.now()}@example.com`;
}

// Note: console error assertions are implemented per-test via page.on('console', ...)
// because Playwright does not provide a built-in way to query past console messages.

test.describe('Demo Web Shop - Header navigation, registration/login, search, PDP', () => {
  test('Navigate to home via site logo from a product details page', async ({ page }) => {
    await page.goto('/build-your-own-computer');
    await page.getByRole('link', { name: 'Tricentis Demo Web Shop' }).click();
    await expect(page).toHaveURL(/\/$/);
    await expect(page).toHaveTitle(/Demo Web Shop$/);
  });

  test.describe('Navigate to a top category from various starting pages', () => {
    const cases: Array<{ startingPage: string; categoryName: string; expectedPath: string }> = [
      { startingPage: 'Home', categoryName: 'Books', expectedPath: '/books' },
      { startingPage: 'Search results', categoryName: 'Computers', expectedPath: '/computers' },
      { startingPage: 'Product details', categoryName: 'Electronics', expectedPath: '/electronics' },
      { startingPage: 'Shopping cart', categoryName: 'Apparel & Shoes', expectedPath: '/apparel-shoes' },
      { startingPage: 'Wishlist', categoryName: 'Digital downloads', expectedPath: '/digital-downloads' },
      { startingPage: 'Register', categoryName: 'Jewelry', expectedPath: '/jewelry' },
      { startingPage: 'Login', categoryName: 'Gift Cards', expectedPath: '/gift-cards' }
    ];

    for (const c of cases) {
      test(`Starting from ${c.startingPage} -> ${c.categoryName}`, async ({ page }) => {
        const consoleErrors: string[] = [];
        page.on('console', (msg) => {
          if (msg.type() === 'error') {
            const text = msg.text();
            if (!/addthis_widget\.js/i.test(text)) consoleErrors.push(text);
          }
        });

        // Given I am on "<startingPage>"
        switch (c.startingPage) {
          case 'Home':
            await page.goto('/');
            break;
          case 'Search results':
            await page.goto('/');
            await page.locator('#small-searchterms').fill('computer');
            await page.locator('#small-searchterms').press('Enter');
            await expect(page).toHaveURL(/\/search\?q=computer/);
            break;
          case 'Product details':
            await page.goto('/build-your-own-computer');
            break;
          case 'Shopping cart':
            await page.goto('/cart');
            break;
          case 'Wishlist':
            await page.goto('/wishlist');
            break;
          case 'Register':
            await page.goto('/register');
            break;
          case 'Login':
            await page.goto('/login');
            break;
          default:
            throw new Error(`Unhandled startingPage: ${c.startingPage}`);
        }

        // When I click the top header category "<categoryName>"
        await page.getByRole('link', { name: c.categoryName }).first().click();

        // Then I should be on the "<categoryName>" category listing page
        await expect(page).toHaveURL(new RegExp(`${c.expectedPath.replace('/', '\\/')}(\\?.*)?$`));
        await expect(page.getByRole('heading', { name: c.categoryName })).toBeVisible();

        // And the category page layout should render without errors
        expect(consoleErrors, `Console errors on ${c.categoryName} page`).toEqual([]);
      });
    }
  });

  test('Navigate to Shopping cart from header (with at least 1 item present)', async ({ page }) => {
    await page.goto('/computing-and-internet');
    await page.locator('#add-to-cart-button-13').click();
    await expect(page.getByRole('link', { name: /Shopping cart \(\d+\)/ })).toContainText('Shopping cart (1)');

    await page.getByRole('link', { name: /Shopping cart \(\d+\)/ }).click();
    await expect(page).toHaveURL(/\/cart/);
    await expect(page.getByRole('heading', { name: 'Shopping cart' })).toBeVisible();
  });

  test('Navigate to Wishlist from header (empty wishlist is a valid state)', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: /Wishlist \(\d+\)/ }).click();
    await expect(page).toHaveURL(/\/wishlist/);
    await expect(page.getByRole('heading', { name: 'Wishlist' })).toBeVisible();
  });

  test('Registration required-field validation prevents submission', async ({ page }) => {
    await page.goto('/register');
    await page.getByRole('button', { name: 'Register' }).click();

    await expect(page.getByText('First name is required.')).toBeVisible();
    await expect(page.getByText('Last name is required.')).toBeVisible();
    await expect(page.getByText('Email is required.')).toBeVisible();
    await expect(page.getByText('Password is required.')).toBeVisible();
  });

  test('Register successfully with valid required fields', async ({ page }) => {
    await page.goto('/register');

    const email = uniqueEmail('new.user');
    await page.getByRole('textbox', { name: 'First name:' }).fill('New');
    await page.getByRole('textbox', { name: 'Last name:' }).fill('User');
    await page.getByRole('textbox', { name: 'Email:' }).fill(email);
    await page.getByRole('textbox', { name: 'Password:', exact: true }).fill('P@ssw0rd123');
    await page.getByRole('textbox', { name: 'Confirm password:' }).fill('P@ssw0rd123');

    await page.getByRole('button', { name: 'Register' }).click();

    await expect(page).toHaveURL(/\/registerresult\/1/);
    await expect(page.getByText('Your registration completed')).toBeVisible();

    // header shows email and logout
    await expect(page.getByRole('link', { name: email })).toBeVisible();
    await expect(page.getByRole('link', { name: /Log out/i })).toBeVisible();

    // Cleanup: log out
    await page.getByRole('link', { name: /Log out/i }).click();
    await expect(page.getByRole('link', { name: 'Log in' })).toBeVisible();
  });

  test('Login fails with invalid credentials shows error', async ({ page }) => {
    await page.goto('/login');
    await page.locator('#Email').fill('user1@example.com');
    await page.locator('#Password').fill('WrongPassword!');
    await page.getByRole('button', { name: 'Log in' }).click();

    await expect(page.getByText('Login was unsuccessful. Please correct the errors and try again.')).toBeVisible();
    await expect(page.getByText('The credentials provided are incorrect')).toBeVisible();
  });

  test('Forgot password link navigates to password recovery (if present)', async ({ page }) => {
    await page.goto('/login');
    const forgot = page.getByRole('link', { name: 'Forgot password?' });
    await expect(forgot).toBeVisible();
    await forgot.click();
    await expect(page).toHaveURL(/\/passwordrecovery/);
  });

  test('Search: keyword with no matches shows no-results message', async ({ page }) => {
    await page.goto('/');
    await page.locator('#small-searchterms').fill('no-such-product-keyword-12345');
    await page.locator('#small-searchterms').press('Enter');

    await expect(page).toHaveURL(/\/search\?q=/);
    await expect(page.getByText('No products were found that matched your criteria.')).toBeVisible();
  });

  test('Search: empty/blank keyword shows minimum length validation', async ({ page }) => {
    await page.goto('/');
    await page.locator('#small-searchterms').fill('   ');
    await page.locator('#small-searchterms').press('Enter');

    await expect(page.getByText(/Search term minimum length is 3 characters/i)).toBeVisible();
  });

  test('Search: special characters render safely (non-script) - !@#$...', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const text = msg.text();
        if (!/addthis_widget\.js/i.test(text)) consoleErrors.push(text);
      }
    });

    await page.goto('/');
    await page.locator('#small-searchterms').fill('!@#$%^&*()_+');
    await page.locator('#small-searchterms').press('Enter');

    await expect(page).toHaveURL(/\/search\?q=/);
    await expect(page.getByRole('heading', { name: 'Search' })).toBeVisible();
    expect(consoleErrors).toEqual([]);
  });

  test('PDP: shows name, price and Add to cart action', async ({ page }) => {
    await page.goto('/computing-and-internet');
    await expect(page.getByRole('heading', { name: 'Computing and Internet' })).toBeVisible();
    await expect(page.getByText(/Price:/)).toBeVisible();
    await expect(page.getByRole('button', { name: 'Add to cart' })).toBeVisible();
  });

  test('PDP: Add to cart updates header cart count', async ({ page }) => {
    await page.goto('/computing-and-internet');

    const cartLink = page.getByRole('link', { name: /Shopping cart \(\d+\)/ });
    const beforeText = await cartLink.innerText();
    const before = Number((beforeText.match(/\((\d+)\)/) ?? [])[1] ?? 0);

    await page.locator('#add-to-cart-button-13').click();
    await expect(cartLink).toContainText(`Shopping cart (${before + 1})`);
  });

  test('PDP: required attributes validation (Build your own computer requires HDD selection)', async ({ page }) => {
    await page.goto('/build-your-own-computer');
    await page.locator('#add-to-cart-button-16').click();

    await expect(page.getByText(/Please select HDD/i)).toBeVisible();
  });

  test('Product not found shows an error page', async ({ page }) => {
    // Substitution: PDP direct navigation for non-existing ID is not directly available via stable route;
    // verify the site provides a clear error page for a bad product route.
    await page.goto(`${BASE}/nonexistent-999999`);
    await expect(page).toHaveTitle(/Error/i);
    await expect(page.getByText(/internal error occurred/i)).toBeVisible();
  });
});
