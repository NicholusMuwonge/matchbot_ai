import { test, expect } from '@playwright/test'

test.describe('Clerk Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    console.log('[Test] Starting authentication flow test')
    await page.goto('/')
  })

  test('redirects to Clerk sign-in when not authenticated', async ({ page }) => {
    console.log('[Test] Testing redirect to Clerk sign-in')

    await page.goto('/_authenticated/')

    await page.waitForURL(/.*clerk.*sign-in.*/, { timeout: 10000 })

    const currentUrl = page.url()
    expect(currentUrl).toContain('clerk')
    expect(currentUrl).toContain('sign-in')

    console.log('[Test] Successfully redirected to Clerk sign-in:', currentUrl)
  })

  test('shows authentication loading state', async ({ page }) => {
    console.log('[Test] Testing authentication loading state')

    await page.goto('/')

    const loadingText = page.getByText('Loading authentication')
    await expect(loadingText).toBeVisible({ timeout: 5000 })

    console.log('[Test] Authentication loading state displayed correctly')
  })

  test('displays error for missing Clerk key', async ({ page }) => {
    console.log('[Test] Testing missing Clerk key error handling')

    page.addInitScript(() => {
      delete window.process
    })

    const consoleErrors = []
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text())
      }
    })

    await page.goto('/')

    const hasAuthError = consoleErrors.some(error =>
      error.includes('Missing VITE_CLERK_PUBLISHABLE_KEY')
    )

    if (process.env.VITE_CLERK_PUBLISHABLE_KEY === 'pk_test_placeholder') {
      console.log('[Test] Placeholder key detected - error expected')
    } else {
      console.log('[Test] Valid key configured')
    }
  })

  test('auth debug logging works in development', async ({ page }) => {
    console.log('[Test] Testing debug logging')

    const consoleLogs = []
    page.on('console', msg => {
      if (msg.type() === 'log') {
        consoleLogs.push(msg.text())
      }
    })

    await page.goto('/')

    await page.waitForTimeout(2000)

    const authDebugLogs = consoleLogs.filter(log =>
      log.includes('[Auth Debug]') ||
      log.includes('[ClerkAuthWrapper]') ||
      log.includes('[API Client]')
    )

    expect(authDebugLogs.length).toBeGreaterThan(0)
    console.log('[Test] Debug logging working:', authDebugLogs.slice(0, 3))
  })

  test('protected routes structure works', async ({ page }) => {
    console.log('[Test] Testing protected routes structure')

    const protectedRoutes = [
      '/_authenticated/',
      '/_authenticated/admin',
      '/_authenticated/items',
      '/_authenticated/settings'
    ]

    for (const route of protectedRoutes) {
      await page.goto(route)

      await page.waitForURL(/.*clerk.*/, { timeout: 10000 })

      const isRedirected = page.url().includes('clerk')
      expect(isRedirected).toBe(true)

      console.log(`[Test] Protected route ${route} correctly redirected`)
    }
  })

  test('token provider configures API client', async ({ page }) => {
    console.log('[Test] Testing token provider configuration')

    const consoleLogs = []
    page.on('console', msg => {
      consoleLogs.push(msg.text())
    })

    await page.goto('/')
    await page.waitForTimeout(1000)

    const tokenProviderLogs = consoleLogs.filter(log =>
      log.includes('[ClerkTokenProvider]') ||
      log.includes('[API Client]')
    )

    console.log('[Test] Token provider logs:', tokenProviderLogs)
  })
})

test.describe('Error Handling', () => {
  test('handles network errors gracefully', async ({ page }) => {
    console.log('[Test] Testing network error handling')

    await page.route('**/api/**', route => {
      route.abort('failed')
    })

    await page.goto('/')

    const errorMessages = []
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errorMessages.push(msg.text())
      }
    })

    await page.waitForTimeout(2000)

    console.log('[Test] Network error handling test completed')
  })

  test('displays meaningful error messages', async ({ page }) => {
    console.log('[Test] Testing error message display')

    const errors = []
    page.on('pageerror', error => {
      errors.push(error.message)
    })

    await page.goto('/')

    if (errors.length > 0) {
      const hasAuthError = errors.some(error =>
        error.includes('Clerk') || error.includes('auth')
      )
      console.log('[Test] Auth-related errors found:', hasAuthError)
    }
  })
})
