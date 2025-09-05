import { type Page, expect, test } from "@playwright/test"

import { randomEmail, randomPassword } from "./utils/random"

test.use({ storageState: { cookies: [], origins: [] } })

// Helper function to fill Clerk sign-up form
const fillClerkSignUpForm = async (
  page: Page,
  firstName: string,
  lastName: string,
  email: string,
  password: string,
) => {
  // Wait for Clerk SignUp component to load
  await page.waitForSelector('[data-clerk-element="sign-up"]', {
    timeout: 10000,
  })

  // Fill first name
  await page.fill('input[name="firstName"]', firstName)

  // Fill last name
  await page.fill('input[name="lastName"]', lastName)

  // Fill email
  await page.fill('input[name="emailAddress"]', email)

  // Fill password
  await page.fill('input[name="password"]', password)
}

// Helper to verify Clerk signup form is visible
const verifyClerkSignUpFormVisible = async (page: Page) => {
  await page.waitForSelector('[data-clerk-element="sign-up"]', {
    timeout: 10000,
  })
  await expect(page.locator('input[name="firstName"]')).toBeVisible()
  await expect(page.locator('input[name="lastName"]')).toBeVisible()
  await expect(page.locator('input[name="emailAddress"]')).toBeVisible()
  await expect(page.locator('input[name="password"]')).toBeVisible()
}

test("Clerk SignUp form fields are visible and editable", async ({ page }) => {
  await page.goto("/signup")

  await verifyClerkSignUpFormVisible(page)

  // Verify all fields are editable
  await expect(page.locator('input[name="firstName"]')).toBeEditable()
  await expect(page.locator('input[name="lastName"]')).toBeEditable()
  await expect(page.locator('input[name="emailAddress"]')).toBeEditable()
  await expect(page.locator('input[name="password"]')).toBeEditable()
})

test("Clerk Sign Up button is visible", async ({ page }) => {
  await page.goto("/signup")

  await page.waitForSelector('[data-clerk-element="sign-up"]', {
    timeout: 10000,
  })
  await expect(page.locator('button[type="submit"]')).toBeVisible()
})

test("Sign In link is visible in Clerk SignUp", async ({ page }) => {
  await page.goto("/signup")

  await page.waitForSelector('[data-clerk-element="sign-up"]', {
    timeout: 10000,
  })
  // Clerk typically shows a sign in link at the bottom
  await expect(
    page.locator('a[href*="signin"], a:has-text("Sign in")'),
  ).toBeVisible()
})

test("Sign up with valid information", async ({ page }) => {
  const firstName = "Test"
  const lastName = "User"
  const email = randomEmail()
  const password = randomPassword()

  await page.goto("/signup")
  await fillClerkSignUpForm(page, firstName, lastName, email, password)
  await page.click('button[type="submit"]')

  // Clerk may require email verification - check for verification step
  // This will depend on your Clerk configuration
  await page.waitForSelector(
    'text="Verify your email", text="Check your email"',
    { timeout: 10000 },
  )
})

test("Sign up with invalid email shows Clerk validation", async ({ page }) => {
  await page.goto("/signup")

  await fillClerkSignUpForm(
    page,
    "Playwright",
    "Test",
    "invalid-email",
    "changethis123",
  )
  await page.click('button[type="submit"]')

  // Clerk will show validation error for invalid email
  await expect(page.locator('[role="alert"], .cl-formFieldError')).toBeVisible()
})

test("Sign up with existing email shows Clerk error", async ({ page }) => {
  const firstName = "Test"
  const lastName = "User"
  const email = randomEmail()
  const password = randomPassword()

  // First signup attempt
  await page.goto("/signup")
  await fillClerkSignUpForm(page, firstName, lastName, email, password)
  await page.click('button[type="submit"]')

  // Wait for potential verification or completion
  await page.waitForTimeout(2000)

  // Second signup attempt with same email
  await page.goto("/signup")
  await fillClerkSignUpForm(page, firstName, lastName, email, password)
  await page.click('button[type="submit"]')

  // Clerk will show error for existing email
  await expect(page.locator('[role="alert"], .cl-formFieldError')).toBeVisible()
})

test("Sign up with weak password shows Clerk validation", async ({ page }) => {
  const firstName = "Test"
  const lastName = "User"
  const email = randomEmail()
  const password = "weak"

  await page.goto("/signup")

  await fillClerkSignUpForm(page, firstName, lastName, email, password)
  await page.click('button[type="submit"]')

  // Clerk will show password strength requirements
  await expect(page.locator('[role="alert"], .cl-formFieldError')).toBeVisible()
})

test("Clerk handles password confirmation automatically", async ({ page }) => {
  // Note: Clerk typically doesn't use separate password confirmation fields
  // This test verifies that Clerk's single password field works correctly
  const firstName = "Test"
  const lastName = "User"
  const email = randomEmail()
  const password = randomPassword()

  await page.goto("/signup")

  await fillClerkSignUpForm(page, firstName, lastName, email, password)

  // Verify that only one password field exists (Clerk's standard)
  const passwordFields = await page.locator('input[name="password"]').count()
  expect(passwordFields).toBe(1)
})

test("Sign up with missing first name shows Clerk validation", async ({
  page,
}) => {
  const firstName = ""
  const lastName = "User"
  const email = randomEmail()
  const password = randomPassword()

  await page.goto("/signup")

  await fillClerkSignUpForm(page, firstName, lastName, email, password)
  await page.click('button[type="submit"]')

  // Clerk will show validation error for required first name
  await expect(page.locator('[role="alert"], .cl-formFieldError')).toBeVisible()
})

test("Sign up with missing email shows Clerk validation", async ({ page }) => {
  const firstName = "Test"
  const lastName = "User"
  const email = ""
  const password = randomPassword()

  await page.goto("/signup")

  await fillClerkSignUpForm(page, firstName, lastName, email, password)
  await page.click('button[type="submit"]')

  // Clerk will show validation error for required email
  await expect(page.locator('[role="alert"], .cl-formFieldError')).toBeVisible()
})

test("Sign up with missing password shows Clerk validation", async ({
  page,
}) => {
  const firstName = "Test"
  const lastName = "User"
  const email = randomEmail()
  const password = ""

  await page.goto("/signup")

  await fillClerkSignUpForm(page, firstName, lastName, email, password)
  await page.click('button[type="submit"]')

  // Clerk will show validation error for required password
  await expect(page.locator('[role="alert"], .cl-formFieldError')).toBeVisible()
})
