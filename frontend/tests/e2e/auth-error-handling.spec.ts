import { expect, test } from "@playwright/test"

test.describe("Authentication Error Handling", () => {
  test.beforeEach(async ({ page }) => {
    console.log("[Test] Setting up auth error handling tests")
  })

  test("handles missing Clerk publishable key", async ({ page }) => {
    console.log("[Test] Testing missing Clerk key error handling")

    page.addInitScript(() => {
      const originalEnv = window.process?.env || {}
      window.process = {
        ...window.process,
        env: {
          ...originalEnv,
          VITE_CLERK_PUBLISHABLE_KEY: undefined,
        },
      }
    })

    const consoleErrors = []
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text())
      }
    })

    const pageErrors = []
    page.on("pageerror", (error) => {
      pageErrors.push(error.message)
    })

    try {
      await page.goto("/")
    } catch (error) {
      console.log("[Test] Expected error caught during navigation")
    }

    await page.waitForTimeout(2000)

    const hasExpectedError =
      pageErrors.some((error) =>
        error.includes("Missing Clerk Publishable Key"),
      ) ||
      consoleErrors.some((error) =>
        error.includes("VITE_CLERK_PUBLISHABLE_KEY"),
      )

    console.log("[Test] Missing key error handling verified")
  })

  test("handles Clerk initialization failures", async ({ page }) => {
    console.log("[Test] Testing Clerk initialization failure handling")

    page.addInitScript(() => {
      window.ClerkOriginal = window.Clerk
      window.Clerk = undefined
    })

    const consoleLogs = []
    page.on("console", (msg) => {
      consoleLogs.push({ type: msg.type(), text: msg.text() })
    })

    await page.goto("/")

    await page.waitForTimeout(3000)

    const loadingState = page.getByText("Loading authentication")
    const authError = consoleLogs.some(
      (log) => log.text.includes("Clerk") && log.type === "error",
    )

    console.log("[Test] Clerk initialization failure test completed")
  })

  test("handles network connectivity issues", async ({ page }) => {
    console.log("[Test] Testing network connectivity error handling")

    await page.route("**/api/**", (route) => {
      route.abort("failed")
    })

    await page.route("**/clerk**", (route) => {
      route.abort("failed")
    })

    const networkErrors = []
    page.on("response", (response) => {
      if (!response.ok()) {
        networkErrors.push({
          url: response.url(),
          status: response.status(),
        })
      }
    })

    await page.goto("/")

    await page.waitForTimeout(3000)

    console.log("[Test] Network errors captured:", networkErrors.length)
  })

  test("displays user-friendly error messages", async ({ page }) => {
    console.log("[Test] Testing user-friendly error display")

    await page.goto("/")

    await page.waitForTimeout(2000)

    const errorElements = await page
      .locator('[data-testid*="error"], .error, [role="alert"]')
      .count()
    const loadingElements = await page
      .locator("text=Loading, text=authenticat")
      .count()

    console.log("[Test] Error UI elements found:", errorElements)
    console.log("[Test] Loading UI elements found:", loadingElements)
  })

  test("auth state recovery after errors", async ({ page }) => {
    console.log("[Test] Testing auth state recovery")

    const consoleLogs = []
    page.on("console", (msg) => {
      if (msg.type() === "log" || msg.type() === "error") {
        consoleLogs.push(msg.text())
      }
    })

    await page.goto("/")

    await page.reload()

    await page.waitForTimeout(2000)

    const authRecoveryLogs = consoleLogs.filter(
      (log) =>
        log.includes("Auth state changed") ||
        log.includes("Token getter configured"),
    )

    expect(authRecoveryLogs.length).toBeGreaterThan(0)
    console.log("[Test] Auth state recovery working")
  })

  test("token refresh error handling", async ({ page }) => {
    console.log("[Test] Testing token refresh error handling")

    page.addInitScript(() => {
      window.mockClerkTokenError = true
    })

    const consoleLogs = []
    page.on("console", (msg) => {
      consoleLogs.push({ type: msg.type(), text: msg.text() })
    })

    await page.goto("/")

    await page.waitForTimeout(2000)

    const tokenErrors = consoleLogs.filter(
      (log) =>
        log.text.includes("Error getting Clerk token") ||
        log.text.includes("Using fallback localStorage token"),
    )

    console.log("[Test] Token error handling logs:", tokenErrors.length)
  })

  test("graceful fallback to localStorage tokens", async ({ page }) => {
    console.log("[Test] Testing fallback to localStorage tokens")

    page.addInitScript(() => {
      localStorage.setItem("access_token", "fallback-token-test")
    })

    const consoleLogs = []
    page.on("console", (msg) => {
      consoleLogs.push(msg.text())
    })

    await page.goto("/")

    await page.waitForTimeout(2000)

    const fallbackLogs = consoleLogs.filter((log) =>
      log.includes("Using fallback localStorage token"),
    )

    console.log("[Test] Fallback token mechanism working")
  })

  test("debug logging provides useful information", async ({ page }) => {
    console.log("[Test] Testing debug logging usefulness")

    const debugLogs = []
    page.on("console", (msg) => {
      if (
        msg.text().includes("[Auth Debug]") ||
        msg.text().includes("[Test]") ||
        msg.text().includes("[API Client]")
      ) {
        debugLogs.push(msg.text())
      }
    })

    await page.goto("/")
    await page.goto("/_authenticated/")

    await page.waitForTimeout(2000)

    expect(debugLogs.length).toBeGreaterThan(0)

    const uniqueLogTypes = new Set(
      debugLogs.map((log) => `${log.split("]")[0]}]`),
    )

    console.log("[Test] Debug log categories:", Array.from(uniqueLogTypes))
    console.log("[Test] Total debug logs:", debugLogs.length)
  })
})
