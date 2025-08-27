/**
 * Vitest configuration for the frontend project
 */

import { defineConfig } from 'vitest/config'
import { resolve } from 'path'
import react from '@vitejs/plugin-react-swc'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/features/auth/tests/test-setup.ts'],
    include: [
      'src/**/*.{test,spec}.{ts,tsx}',
      // Exclude e2e tests to avoid mixing with unit tests
      '!src/**/*.e2e.{test,spec}.{ts,tsx}',
      '!src/**/e2e/**',
    ],
    exclude: [
      'node_modules',
      'dist',
      // Exclude root level tests that are likely Playwright e2e tests
      'tests/**',
    ],
    env: {
      VITE_API_URL: 'http://localhost:8000',
      VITE_CLERK_PUBLISHABLE_KEY: 'pk_test_example',
    },
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
})
