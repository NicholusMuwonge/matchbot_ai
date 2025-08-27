/**
 * Simplified auth theme utilities using Chakra UI v3 native color mode
 * This file now only contains utility functions that complement Chakra's built-in theming
 */

/**
 * Badge color schemes for different user states
 * Uses Chakra UI's native colorScheme prop values
 */
export const getBadgeColorScheme = (
  type: 'active' | 'inactive' | 'verified' | 'pending' | 'clerk'
): string => {
  switch (type) {
    case 'active':
    case 'verified':
      return 'green'
    case 'inactive':
      return 'red'
    case 'pending':
      return 'orange'
    case 'clerk':
      return 'blue'
    default:
      return 'gray'
  }
}

/**
 * Get appropriate variant for badges
 */
export const getBadgeVariant = () => 'subtle' as const

/**
 * Common color values for auth components
 * These complement Chakra's semantic tokens
 */
export const authColorTokens = {
  primary: { base: '#2463eb', _dark: '#4299e1' },
  surface: { base: 'white', _dark: 'gray.800' },
  background: { base: 'gray.50', _dark: 'gray.900' },
  text: {
    primary: { base: 'gray.900', _dark: 'white' },
    secondary: { base: 'gray.600', _dark: 'gray.300' },
  },
  border: {
    default: { base: 'gray.200', _dark: 'gray.600' },
    error: { base: 'red.200', _dark: 'red.600' },
  },
  status: {
    error: { base: 'red.50', _dark: 'red.900' },
    success: { base: 'green.50', _dark: 'green.900' },
  },
}
