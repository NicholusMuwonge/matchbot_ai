import { test as setup } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"

const authFile = "playwright/.auth/user.json"

setup("authenticate", async ({ page }) => {
  // Navigate to sign in page
  await page.goto("/signin")

  // Wait for Clerk SignIn component to load
  await page.waitForSelector('[data-clerk-element="sign-in"]', {
    timeout: 10000,
  })

  // Fill in credentials using Clerk's form structure
  // Clerk forms may have different selectors
  await page.fill('input[name="identifier"]', firstSuperuser)
  await page.click('button[type="submit"]')

  // Wait for password field to appear (Clerk's two-step flow)
  await page.waitForSelector('input[name="password"]', { timeout: 5000 })
  await page.fill('input[name="password"]', firstSuperuserPassword)
  await page.click('button[type="submit"]')

  // Wait for successful authentication and redirect
  await page.waitForURL("/")
  await page.context().storageState({ path: authFile })
})
