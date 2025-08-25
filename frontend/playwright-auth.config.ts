import { defineConfig } from "@playwright/test"

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ["html", { outputFolder: "playwright-report/auth" }],
    ["json", { outputFile: "test-results/auth-results.json" }],
  ],
  outputDir: "test-results/auth/",

  use: {
    baseURL: "http://localhost:5174",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },

  projects: [
    {
      name: "clerk-auth-tests",
      testMatch: /clerk-auth-flow\.spec\.ts/,
    },
    {
      name: "protected-routes-tests",
      testMatch: /protected-routes\.spec\.ts/,
    },
    {
      name: "error-handling-tests",
      testMatch: /auth-error-handling\.spec\.ts/,
    },
  ],

  webServer: {
    command: "npm run dev",
    url: "http://localhost:5174",
    reuseExistingServer: !process.env.CI,
  },
})
