import { type Page, expect, test } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"
import { randomPassword } from "./utils/random.ts"

test.use({ storageState: { cookies: [], origins: [] } })

// Helper function to fill Clerk sign-in form
const fillClerkSignInForm = async (page: Page, email: string, password: string) => {
  // Wait for Clerk SignIn component to load
  await page.waitForSelector('[data-clerk-element="sign-in"]', { timeout: 10000 })

  // Fill email/identifier field
  await page.fill('input[name="identifier"]', email)
  await page.click('button[type="submit"]')

  // Wait for password field (Clerk's two-step flow)
  await page.waitForSelector('input[name="password"]', { timeout: 5000 })
  await page.fill('input[name="password"]', password)
}

// Helper to verify Clerk form elements are visible
const verifyClerkFormVisible = async (page: Page) => {
  await page.waitForSelector('[data-clerk-element="sign-in"]', { timeout: 10000 })
  await expect(page.locator('input[name="identifier"]')).toBeVisible()
}

test("Clerk SignIn form is visible and functional", async ({ page }) => {
  await page.goto("/signin")

  await verifyClerkFormVisible(page)
  await expect(page.locator('input[name="identifier"]')).toBeEditable()
})

test("Clerk Continue/Sign In button is visible", async ({ page }) => {
  await page.goto("/signin")

  await page.waitForSelector('[data-clerk-element="sign-in"]', { timeout: 10000 })
  await expect(page.locator('button[type="submit"]').first()).toBeVisible()
})

test("Clerk Forgot Password link is accessible", async ({ page }) => {
  await page.goto("/signin")

  await page.waitForSelector('[data-clerk-element="sign-in"]', { timeout: 10000 })
  // Clerk typically shows forgot password after entering email
  await page.fill('input[name="identifier"]', firstSuperuser)
  await page.click('button[type="submit"]')

  // Check for forgot password link in Clerk's password step
  await page.waitForSelector('a[href*="forgot-password"], button:has-text("Forgot password")', { timeout: 5000 })
})

test("Log in with valid email and password", async ({ page }) => {
  await page.goto("/signin")

  await fillClerkSignInForm(page, firstSuperuser, firstSuperuserPassword)
  await page.click('button[type="submit"]')

  await page.waitForURL("/")

  // Check for successful login - dashboard or welcome message
  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()
})

test("Log in with invalid email shows Clerk error", async ({ page }) => {
  await page.goto("/signin")

  await page.waitForSelector('[data-clerk-element="sign-in"]', { timeout: 10000 })
  await page.fill('input[name="identifier"]', "invalidemail")
  await page.click('button[type="submit"]')

  // Clerk will show validation error for invalid email format
  await expect(page.locator('[role="alert"], .cl-formFieldError')).toBeVisible()
})

test("Log in with invalid password shows Clerk error", async ({ page }) => {
  const password = randomPassword()

  await page.goto("/signin")
  await fillClerkSignInForm(page, firstSuperuser, password)
  await page.click('button[type="submit"]')

  // Clerk will show authentication error
  await expect(page.locator('[role="alert"], .cl-formFieldError')).toBeVisible()
})

// Log out

test("Successful log out using Clerk UserButton", async ({ page }) => {
  await page.goto("/signin")

  await fillClerkSignInForm(page, firstSuperuser, firstSuperuserPassword)
  await page.click('button[type="submit"]')

  await page.waitForURL("/")

  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()

  // Click on Clerk UserButton (now in user-menu test id)
  await page.getByTestId("user-menu").click()

  // Clerk UserButton opens a popover/menu - look for sign out option
  await page.waitForSelector('[data-clerk-element="userButton"] button:has-text("Sign out"), button:has-text("Sign out")', { timeout: 5000 })
  await page.click('button:has-text("Sign out")')

  await page.waitForURL("/signin")
})

test("Logged-out user cannot access protected routes", async ({ page }) => {
  await page.goto("/signin")

  await fillClerkSignInForm(page, firstSuperuser, firstSuperuserPassword)
  await page.click('button[type="submit"]')

  await page.waitForURL("/")

  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()

  // Sign out using Clerk UserButton
  await page.getByTestId("user-menu").click()
  await page.waitForSelector('button:has-text("Sign out")', { timeout: 5000 })
  await page.click('button:has-text("Sign out")')
  await page.waitForURL("/signin")

  // Try to access protected route
  await page.goto("/settings")
  await page.waitForURL("/signin")
})

test("Redirects to /signin when not authenticated with Clerk", async ({ page }) => {
  // Clear any existing Clerk session
  await page.goto("/signin")
  await page.evaluate(() => {
    // Clear all localStorage and sessionStorage
    localStorage.clear()
    sessionStorage.clear()
  })

  // Try to access protected route without authentication
  await page.goto("/settings")
  await page.waitForURL("/signin")
  await expect(page).toHaveURL("/signin")
})
