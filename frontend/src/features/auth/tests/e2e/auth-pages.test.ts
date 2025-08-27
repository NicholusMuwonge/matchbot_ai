/**
 * E2E tests for auth pages and flows
 */

import { type Page, expect, test } from "@playwright/test"

// Test configuration
test.use({ storageState: { cookies: [], origins: [] } })

// Helper functions
const fillClerkSignInForm = async (
  page: Page,
  email: string,
  password: string,
) => {
  await page.waitForSelector('[data-clerk-element="sign-in"]', {
    timeout: 10000,
  })
  await page.fill('input[name="identifier"]', email)
  await page.click('button[type="submit"]')
  await page.waitForSelector('input[name="password"]', { timeout: 5000 })
  await page.fill('input[name="password"]', password)
  await page.click('button[type="submit"]')
}

const signOutWithClerk = async (page: Page) => {
  await page.getByTestId("user-menu").click()
  await page.waitForSelector('button:has-text("Sign out")', { timeout: 5000 })
  await page.click('button:has-text("Sign out")')
  await page.waitForURL("/signin")
}

test.describe("Auth Pages E2E", () => {
  test.beforeEach(async ({ page }) => {
    // Clear any existing auth state
    await page.goto("/signin")
    await page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })
  })

  test("sign in page loads with Clerk component", async ({ page }) => {
    await page.goto("/signin")

    // Verify Clerk SignIn component is loaded
    await expect(page.locator('[data-clerk-element="sign-in"]')).toBeVisible()
    await expect(page.locator('input[name="identifier"]')).toBeVisible()

    // Verify logo and page structure
    await expect(page.locator('img[alt="FastAPI logo"]')).toBeVisible()
  })

  test("sign up page loads with Clerk component", async ({ page }) => {
    await page.goto("/signup")

    // Verify Clerk SignUp component is loaded
    await expect(page.locator('[data-clerk-element="sign-up"]')).toBeVisible()
    await expect(page.locator('input[name="firstName"]')).toBeVisible()
    await expect(page.locator('input[name="lastName"]')).toBeVisible()
    await expect(page.locator('input[name="emailAddress"]')).toBeVisible()
    await expect(page.locator('input[name="password"]')).toBeVisible()

    // Verify logo and page structure
    await expect(page.locator('img[alt="FastAPI logo"]')).toBeVisible()
  })

  test("navigation between sign in and sign up pages", async ({ page }) => {
    await page.goto("/signin")

    // Look for sign up link in Clerk component
    await expect(
      page.locator('a[href*="signup"], a:has-text("Sign up")'),
    ).toBeVisible()

    // Navigate to signup
    await page.goto("/signup")
    await expect(page.locator('[data-clerk-element="sign-up"]')).toBeVisible()

    // Look for sign in link in Clerk component
    await expect(
      page.locator('a[href*="signin"], a:has-text("Sign in")'),
    ).toBeVisible()
  })

  test("sign in form validation", async ({ page }) => {
    await page.goto("/signin")

    await page.waitForSelector('[data-clerk-element="sign-in"]', {
      timeout: 10000,
    })

    // Try to submit without email
    await page.click('button[type="submit"]')

    // Clerk should show validation error
    await expect(
      page.locator('[role="alert"], .cl-formFieldError'),
    ).toBeVisible()

    // Fill invalid email
    await page.fill('input[name="identifier"]', "invalid-email")
    await page.click('button[type="submit"]')

    // Should show email validation error
    await expect(
      page.locator('[role="alert"], .cl-formFieldError'),
    ).toBeVisible()
  })

  test("sign up form validation", async ({ page }) => {
    await page.goto("/signup")

    await page.waitForSelector('[data-clerk-element="sign-up"]', {
      timeout: 10000,
    })

    // Try to submit without required fields
    await page.click('button[type="submit"]')

    // Should show validation errors
    await expect(
      page.locator('[role="alert"], .cl-formFieldError'),
    ).toBeVisible()

    // Fill invalid email
    await page.fill('input[name="emailAddress"]', "invalid-email")
    await page.click('button[type="submit"]')

    // Should show email validation error
    await expect(
      page.locator('[role="alert"], .cl-formFieldError'),
    ).toBeVisible()

    // Fill weak password
    await page.fill('input[name="emailAddress"]', "test@example.com")
    await page.fill('input[name="password"]', "weak")
    await page.click('button[type="submit"]')

    // Should show password validation error
    await expect(
      page.locator('[role="alert"], .cl-formFieldError'),
    ).toBeVisible()
  })

  test("auth guard redirects unauthenticated users", async ({ page }) => {
    // Try to access protected route
    await page.goto("/settings")

    // Should redirect to signin
    await expect(page).toHaveURL("/signin")
    await expect(page.locator('[data-clerk-element="sign-in"]')).toBeVisible()

    // Try admin route
    await page.goto("/admin")

    // Should also redirect to signin
    await expect(page).toHaveURL("/signin")
  })

  test("successful authentication allows access to protected routes", async ({
    page,
  }) => {
    // This test assumes you have valid test credentials in your environment
    const testEmail = process.env.PLAYWRIGHT_TEST_EMAIL || "test@example.com"
    const testPassword =
      process.env.PLAYWRIGHT_TEST_PASSWORD || "testpassword123"

    // Note: This test may need to be skipped if you don't have test credentials
    test.skip(
      !process.env.PLAYWRIGHT_TEST_EMAIL,
      "No test credentials provided",
    )

    await page.goto("/signin")

    // Fill and submit sign in form
    await fillClerkSignInForm(page, testEmail, testPassword)

    // Should redirect to dashboard
    await page.waitForURL("/", { timeout: 10000 })
    await expect(
      page.getByText("Welcome back, nice to see you again!"),
    ).toBeVisible()

    // Should now be able to access protected routes
    await page.goto("/settings")
    await expect(page).toHaveURL("/settings")
    await expect(page.getByText("Profile Settings")).toBeVisible()

    // Should see Clerk UserProfile component
    await expect(
      page.locator('[data-clerk-element="userProfile"]'),
    ).toBeVisible()
  })

  test("user menu displays correctly when authenticated", async ({ page }) => {
    // This test assumes authentication was successful in previous test or setup
    test.skip(
      !process.env.PLAYWRIGHT_TEST_EMAIL,
      "No test credentials provided",
    )

    const testEmail = process.env.PLAYWRIGHT_TEST_EMAIL || "test@example.com"
    const testPassword =
      process.env.PLAYWRIGHT_TEST_PASSWORD || "testpassword123"

    await page.goto("/signin")
    await fillClerkSignInForm(page, testEmail, testPassword)
    await page.waitForURL("/")

    // Should see user menu
    await expect(page.getByTestId("user-menu")).toBeVisible()

    // Click user menu to see Clerk UserButton options
    await page.getByTestId("user-menu").click()

    // Should see sign out option
    await expect(page.locator('button:has-text("Sign out")')).toBeVisible()
  })

  test("sign out flow works correctly", async ({ page }) => {
    test.skip(
      !process.env.PLAYWRIGHT_TEST_EMAIL,
      "No test credentials provided",
    )

    const testEmail = process.env.PLAYWRIGHT_TEST_EMAIL || "test@example.com"
    const testPassword =
      process.env.PLAYWRIGHT_TEST_PASSWORD || "testpassword123"

    // Sign in first
    await page.goto("/signin")
    await fillClerkSignInForm(page, testEmail, testPassword)
    await page.waitForURL("/")

    // Sign out
    await signOutWithClerk(page)

    // Should be redirected to sign in page
    await expect(page).toHaveURL("/signin")

    // Should no longer be able to access protected routes
    await page.goto("/settings")
    await expect(page).toHaveURL("/signin")
  })

  test("admin user list page loads for authenticated users", async ({
    page,
  }) => {
    test.skip(
      !process.env.PLAYWRIGHT_TEST_EMAIL,
      "No test credentials provided",
    )

    const testEmail = process.env.PLAYWRIGHT_TEST_EMAIL || "test@example.com"
    const testPassword =
      process.env.PLAYWRIGHT_TEST_PASSWORD || "testpassword123"

    await page.goto("/signin")
    await fillClerkSignInForm(page, testEmail, testPassword)
    await page.waitForURL("/")

    // Navigate to admin page
    await page.goto("/admin")

    // Should see admin page content
    await expect(page.getByText("Users Management")).toBeVisible()

    // Should see both user management sections
    await expect(page.getByText("Traditional User Management")).toBeVisible()
    await expect(page.getByText("Clerk Authentication Status")).toBeVisible()

    // Should see user table (may be loading or show data)
    await expect(page.locator('[data-testid="table-root"]')).toBeVisible()
  })

  test("user settings page shows Clerk UserProfile", async ({ page }) => {
    test.skip(
      !process.env.PLAYWRIGHT_TEST_EMAIL,
      "No test credentials provided",
    )

    const testEmail = process.env.PLAYWRIGHT_TEST_EMAIL || "test@example.com"
    const testPassword =
      process.env.PLAYWRIGHT_TEST_PASSWORD || "testpassword123"

    await page.goto("/signin")
    await fillClerkSignInForm(page, testEmail, testPassword)
    await page.waitForURL("/")

    // Navigate to settings
    await page.goto("/settings")

    // Should see settings page structure
    await expect(page.getByText("User Settings")).toBeVisible()
    await expect(page.getByText("Profile Settings")).toBeVisible()
    await expect(page.getByText("App Preferences")).toBeVisible()

    // Should see Clerk UserProfile component
    await expect(
      page.locator('[data-clerk-element="userProfile"]'),
    ).toBeVisible()
  })

  test("responsive design works on mobile viewport", async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    await page.goto("/signin")

    // Clerk component should still be visible and usable
    await expect(page.locator('[data-clerk-element="sign-in"]')).toBeVisible()
    await expect(page.locator('input[name="identifier"]')).toBeVisible()

    // Logo should still be visible
    await expect(page.locator('img[alt="FastAPI logo"]')).toBeVisible()

    // Check signup page too
    await page.goto("/signup")
    await expect(page.locator('[data-clerk-element="sign-up"]')).toBeVisible()
  })
})
