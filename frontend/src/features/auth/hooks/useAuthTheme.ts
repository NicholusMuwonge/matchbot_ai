/**
 * Hook for auth-specific theme management using Chakra UI native approach
 */

import { useColorMode, useColorModeValue } from '@/components/ui/color-mode'
import { useMemo } from 'react'

export interface AuthThemeHook {
  isDark: boolean
  colorMode: 'light' | 'dark'
  toggleColorMode: () => void
  setColorMode: (mode: 'light' | 'dark') => void
  clerkTheme: Record<string, string>
}

/**
 * Custom hook for managing auth component themes using Chakra's native color mode
 */
export const useAuthTheme = (): AuthThemeHook => {
  const { colorMode, toggleColorMode, setColorMode } = useColorMode()
  const isDark = colorMode === 'dark'

  // Clerk theme configuration using Chakra's color mode values
  const clerkTheme = useMemo(() => ({
    colorPrimary: useColorModeValue('#2463eb', '#4299e1'),
    colorBackground: useColorModeValue('#ffffff', '#1a202c'),
    colorInputBackground: useColorModeValue('#ffffff', '#1a202c'),
    colorInputText: useColorModeValue('#1a202c', '#f7fafc'),
    colorText: useColorModeValue('#1a202c', '#f7fafc'),
    colorTextSecondary: useColorModeValue('#4a5568', '#cbd5e0'),
    colorNeutral: useColorModeValue('#718096', '#a0aec0'),
    borderRadius: '0.375rem',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  }), [colorMode])

  return {
    isDark,
    colorMode,
    toggleColorMode,
    setColorMode,
    clerkTheme,
  }
}

/**
 * Hook for getting Clerk appearance configuration based on current theme
 */
export const useClerkTheme = () => {
  const { clerkTheme, isDark } = useAuthTheme()

  return useMemo(() => ({
    appearance: {
      variables: clerkTheme,
      elements: {
        // Card styling
        card: `
          box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
          border: 1px solid ${isDark ? '#2d3748' : '#e2e8f0'};
          background-color: ${clerkTheme.colorBackground};
        `,

        // Header styling
        headerTitle: `
          color: ${clerkTheme.colorText};
          font-weight: 600;
          text-align: center;
          margin-bottom: 0.5rem;
        `,

        headerSubtitle: `
          color: ${clerkTheme.colorTextSecondary};
          text-align: center;
          margin-bottom: 1.5rem;
        `,

        // Form elements
        formButtonPrimary: `
          width: 100%;
          background-color: ${clerkTheme.colorPrimary};
          border: none;
          color: white;
          font-weight: 500;
          padding: 0.5rem 1rem;
          border-radius: ${clerkTheme.borderRadius};
          transition: background-color 0.2s;

          &:hover {
            background-color: ${isDark ? '#3182ce' : '#1e40af'};
          }

          &:focus {
            outline: 2px solid ${clerkTheme.colorPrimary};
            outline-offset: 2px;
          }
        `,

        formFieldLabel: `
          color: ${clerkTheme.colorText};
          font-weight: 500;
          margin-bottom: 0.25rem;
        `,

        formFieldInput: `
          width: 100%;
          border: 1px solid ${isDark ? '#2d3748' : '#d1d5db'};
          background-color: ${clerkTheme.colorInputBackground};
          color: ${clerkTheme.colorInputText};
          padding: 0.5rem 0.75rem;
          border-radius: ${clerkTheme.borderRadius};
          transition: border-color 0.2s, box-shadow 0.2s;

          &:focus {
            outline: none;
            border-color: ${clerkTheme.colorPrimary};
            box-shadow: 0 0 0 3px ${clerkTheme.colorPrimary}25;
          }
        `,

        // Links and actions
        footerActionLink: `
          color: ${clerkTheme.colorPrimary};
          font-weight: 500;
          text-decoration: none;

          &:hover {
            text-decoration: underline;
          }
        `,

        // Social buttons
        socialButtonsBlockButton: `
          width: 100%;
          border: 1px solid ${isDark ? '#2d3748' : '#d1d5db'};
          background-color: ${clerkTheme.colorBackground};
          color: ${clerkTheme.colorText};
          padding: 0.5rem 1rem;
          border-radius: ${clerkTheme.borderRadius};
          transition: background-color 0.2s;

          &:hover {
            background-color: ${isDark ? '#2d3748' : '#f9fafb'};
          }
        `,

        // Dividers
        dividerLine: `
          background-color: ${isDark ? '#2d3748' : '#e5e7eb'};
        `,

        dividerText: `
          color: ${clerkTheme.colorTextSecondary};
          font-size: 0.75rem;
        `,

        // Alerts and errors
        alertText: `
          color: ${isDark ? '#fc8181' : '#dc2626'};
          font-size: 0.875rem;
        `,

        // Identity preview
        identityPreviewText: `
          color: ${clerkTheme.colorText};
        `,

        // User button (for navigation mode)
        userButtonAvatarBox: `
          width: 2rem;
          height: 2rem;
          border-radius: 50%;
        `,

        userButtonPopoverCard: `
          background-color: ${clerkTheme.colorBackground};
          border: 1px solid ${isDark ? '#2d3748' : '#e2e8f0'};
          border-radius: ${clerkTheme.borderRadius};
          box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        `,

        userButtonPopoverActionButton: `
          color: ${clerkTheme.colorText};
          padding: 0.5rem 0.75rem;
          border-radius: calc(${clerkTheme.borderRadius} - 2px);
          transition: background-color 0.2s;

          &:hover {
            background-color: ${isDark ? '#2d3748' : '#f3f4f6'};
          }
        `,
      },
    },
  }), [isDark, clerkTheme])
}
