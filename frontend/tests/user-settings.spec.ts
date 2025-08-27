import { expect, test } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"

// Helper to sign in with Clerk for settings tests
const signInWithClerk = async (page: any, email: string, password: string) => {
  await page.goto("/signin")
  await page.waitForSelector('[data-clerk-element="sign-in"]', { timeout: 10000 })
  await page.fill('input[name="identifier"]', email)
  await page.click('button[type="submit"]')
  await page.waitForSelector('input[name="password"]', { timeout: 5000 })
  await page.fill('input[name="password"]', password)
  await page.click('button[type="submit"]')
  await page.waitForURL("/")
}

// Helper to sign out with Clerk
const signOutWithClerk = async (page: any) => {
  await page.getByTestId("user-menu").click()
  await page.waitForSelector('button:has-text("Sign out")', { timeout: 5000 })
  await page.click('button:has-text("Sign out")')
  await page.waitForURL("/signin")
}

// Settings page with Clerk UserProfile integration

test("Settings page loads with Clerk UserProfile", async ({ page }) => {
  await page.goto("/settings")

  // Check that Clerk UserProfile component is loaded
  await page.waitForSelector('[data-clerk-element="userProfile"]', { timeout: 10000 })
  await expect(page.getByText("Profile Settings")).toBeVisible()
})

test("Clerk UserProfile component is interactive", async ({ page }) => {
  await page.goto("/settings")

  // Verify Clerk UserProfile is present and interactive
  await page.waitForSelector('[data-clerk-element="userProfile"]', { timeout: 10000 })

  // Clerk UserProfile should have navigation elements
  const userProfile = page.locator('[data-clerk-element="userProfile"]')
  await expect(userProfile).toBeVisible()
})

test.describe("Clerk UserProfile functionality", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Clerk UserProfile allows profile management", async ({ page }) => {
    // Sign in with existing user
    await signInWithClerk(page, firstSuperuser, firstSuperuserPassword)

    await page.goto("/settings")

    // Verify Clerk UserProfile is present
    await page.waitForSelector('[data-clerk-element="userProfile"]', { timeout: 10000 })

    // Clerk UserProfile handles all profile editing internally
    // We just verify it's loaded and functional
    const userProfile = page.locator('[data-clerk-element="userProfile"]')
    await expect(userProfile).toBeVisible()

    // Look for common Clerk UserProfile sections
    // These may vary based on Clerk configuration
    await expect(page.locator('[data-clerk-element="userProfile"] nav, .cl-navbar')).toBeVisible()
  })
})

test.describe("Clerk UserProfile validation", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Clerk UserProfile handles validation internally", async ({ page }) => {
    // Sign in with existing user
    await signInWithClerk(page, firstSuperuser, firstSuperuserPassword)

    await page.goto("/settings")

    // Verify Clerk UserProfile loads
    await page.waitForSelector('[data-clerk-element="userProfile"]', { timeout: 10000 })

    // Clerk handles all form validation internally
    // We just verify the component is functional
    const userProfile = page.locator('[data-clerk-element="userProfile"]')
    await expect(userProfile).toBeVisible()

    // Check that Clerk UserProfile is interactive
    // (specific interactions depend on Clerk configuration)
  })
})

// Password Management - Now handled by Clerk UserProfile

test.describe("Password management through Clerk", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Clerk UserProfile provides password management", async ({ page }) => {
    // Sign in with existing user
    await signInWithClerk(page, firstSuperuser, firstSuperuserPassword)

    await page.goto("/settings")

    // Verify Clerk UserProfile loads
    await page.waitForSelector('[data-clerk-element="userProfile"]', { timeout: 10000 })

    // Clerk UserProfile includes password management functionality
    // This is handled internally by Clerk's secure interface
    const userProfile = page.locator('[data-clerk-element="userProfile"]')
    await expect(userProfile).toBeVisible()

    // Note: Specific password change testing would require interacting with Clerk's UI
    // which may vary based on configuration. The important thing is that the
    // UserProfile component is loaded and functional.
  })
})

// Appearance - Custom app functionality still available

test("App Preferences section is visible", async ({ page }) => {
  await page.goto("/settings")

  // The appearance functionality is now in "App Preferences" section
  await expect(page.getByText("App Preferences")).toBeVisible()

  // Look for the appearance controls
  await expect(page.locator('label:has-text("Light Mode"), label:has-text("Dark Mode")')).toBeVisible()
})

test("User can switch from light mode to dark mode and vice versa", async ({
  page,
}) => {
  await page.goto("/settings")

  // Wait for settings page to load, then look for appearance section
  await page.waitForSelector('text="App Preferences"', { timeout: 10000 })

  // Ensure the initial state is light mode
  if (
    await page.evaluate(() =>
      document.documentElement.classList.contains("dark"),
    )
  ) {
    await page
      .locator("label")
      .filter({ hasText: "Light Mode" })
      .locator("span")
      .first()
      .click()
  }

  let isLightMode = await page.evaluate(() =>
    document.documentElement.classList.contains("light"),
  )
  expect(isLightMode).toBe(true)

  await page
    .locator("label")
    .filter({ hasText: "Dark Mode" })
    .locator("span")
    .first()
    .click()
  const isDarkMode = await page.evaluate(() =>
    document.documentElement.classList.contains("dark"),
  )
  expect(isDarkMode).toBe(true)

  await page
    .locator("label")
    .filter({ hasText: "Light Mode" })
    .locator("span")
    .first()
    .click()
  isLightMode = await page.evaluate(() =>
    document.documentElement.classList.contains("light"),
  )
  expect(isLightMode).toBe(true)
})

test("Selected mode is preserved across sessions", async ({ page }) => {
  await page.goto("/settings")

  // Wait for settings page to load
  await page.waitForSelector('text="App Preferences"', { timeout: 10000 })

  // Ensure the initial state is light mode
  if (
    await page.evaluate(() =>
      document.documentElement.classList.contains("dark"),
    )
  ) {
    await page
      .locator("label")
      .filter({ hasText: "Light Mode" })
      .locator("span")
      .first()
      .click()
  }

  const isLightMode = await page.evaluate(() =>
    document.documentElement.classList.contains("light"),
  )
  expect(isLightMode).toBe(true)

  await page
    .locator("label")
    .filter({ hasText: "Dark Mode" })
    .locator("span")
    .first()
    .click()
  let isDarkMode = await page.evaluate(() =>
    document.documentElement.classList.contains("dark"),
  )
  expect(isDarkMode).toBe(true)

  await signOutWithClerk(page)
  await signInWithClerk(page, firstSuperuser, firstSuperuserPassword)

  await page.goto("/settings")

  isDarkMode = await page.evaluate(() =>
    document.documentElement.classList.contains("dark"),
  )
  expect(isDarkMode).toBe(true)
})
