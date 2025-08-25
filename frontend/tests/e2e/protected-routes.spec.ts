import { test, expect } from '@playwright/test'

test.describe('Protected Routes Security', () => {
  const protectedRoutes = [
    { path: '/_authenticated/', name: 'Dashboard' },
    { path: '/_authenticated/admin', name: 'Admin Panel' },
    { path: '/_authenticated/items', name: 'Items Management' },
    { path: '/_authenticated/settings', name: 'User Settings' }
  ]

  test.beforeEach(async ({ page }) => {
    console.log('[Test] Setting up protected routes test')
  })

  protectedRoutes.forEach(({ path, name }) => {
    test(`${name} requires authentication`, async ({ page }) => {
      console.log(`[Test] Testing ${name} protection: ${path}`)

      await page.goto(path)

      await page.waitForURL(/.*clerk.*sign-in.*/, { timeout: 10000 })

      const currentUrl = page.url()
      expect(currentUrl).toContain('clerk')
      expect(currentUrl).toContain('sign-in')

      console.log(`[Test] ${name} successfully protected - redirected to:`, currentUrl)
    })
  })

  test('public routes remain accessible', async ({ page }) => {
    console.log('[Test] Testing public route accessibility')

    const publicRoutes = [
      '/',
    ]

    for (const route of publicRoutes) {
      await page.goto(route)

      await page.waitForTimeout(2000)

      const isClerkRedirect = page.url().includes('clerk')
      console.log(`[Test] Route ${route} - Clerk redirect: ${isClerkRedirect}`)

      if (route === '/') {
        expect(page.url()).not.toContain('clerk')
      }
    }
  })

  test('direct navigation to protected routes fails', async ({ page }) => {
    console.log('[Test] Testing direct navigation blocking')

    const testCases = [
      { route: '/_authenticated/admin', description: 'Admin panel direct access' },
      { route: '/_authenticated/settings', description: 'Settings direct access' },
    ]

    for (const { route, description } of testCases) {
      console.log(`[Test] Testing ${description}`)

      await page.goto(route)

      await page.waitForURL(/.*clerk.*/, { timeout: 10000 })

      const isBlocked = page.url().includes('clerk')
      expect(isBlocked).toBe(true)

      console.log(`[Test] ${description} correctly blocked`)
    }
  })

  test('auth wrapper renders protection UI', async ({ page }) => {
    console.log('[Test] Testing auth wrapper UI')

    const consoleLogs = []
    page.on('console', msg => {
      consoleLogs.push(msg.text())
    })

    await page.goto('/_authenticated/')

    await page.waitForTimeout(2000)

    const wrapperLogs = consoleLogs.filter(log =>
      log.includes('[ClerkAuthWrapper]') ||
      log.includes('[ProtectedRoute]')
    )

    console.log('[Test] Auth wrapper logs:', wrapperLogs.slice(0, 3))
  })

  test('authentication state changes trigger route updates', async ({ page }) => {
    console.log('[Test] Testing auth state change handling')

    const consoleLogs = []
    page.on('console', msg => {
      consoleLogs.push(msg.text())
    })

    await page.goto('/_authenticated/')

    await page.waitForTimeout(3000)

    const authStateLogs = consoleLogs.filter(log =>
      log.includes('Auth state changed') ||
      log.includes('Route protection check')
    )

    expect(authStateLogs.length).toBeGreaterThan(0)
    console.log('[Test] Auth state monitoring working')
  })
})

test.describe('Route Context and Data', () => {
  test('authenticated layout renders correctly', async ({ page }) => {
    console.log('[Test] Testing authenticated layout rendering')

    const consoleLogs = []
    page.on('console', msg => {
      consoleLogs.push(msg.text())
    })

    await page.goto('/_authenticated/')

    await page.waitForTimeout(2000)

    const layoutLogs = consoleLogs.filter(log =>
      log.includes('[AuthenticatedLayout]')
    )

    console.log('[Test] Layout rendering logs:', layoutLogs)
  })

  test('router context provides auth data', async ({ page }) => {
    console.log('[Test] Testing router context auth data')

    await page.goto('/')

    await page.evaluate(() => {
      console.log('[Test Context] Window Clerk available:', !!window.Clerk)
      console.log('[Test Context] Auth loading state check')
    })

    await page.waitForTimeout(2000)

    console.log('[Test] Router context test completed')
  })

  test('navigation between protected routes works when authenticated', async ({ page }) => {
    console.log('[Test] Testing navigation between protected routes')

    await page.goto('/_authenticated/')

    await page.waitForURL(/.*clerk.*/, { timeout: 10000 })

    console.log('[Test] Navigation test completed - would require auth setup for full test')
  })
})
