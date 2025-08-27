/**
 * Vitest configuration for auth feature tests
 */

import { resolve } from "node:path"
import { defineConfig } from "vitest/config"

export default defineConfig({
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./test-setup.ts"],
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "../../../"),
    },
  },
})
