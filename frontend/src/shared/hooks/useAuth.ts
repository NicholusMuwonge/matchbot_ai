/**
 * Simple auth hook for protected routes
 * Provides authentication state and user info for any protected component
 */

import { useAuth as useClerkAuth } from "@clerk/clerk-react"

export function useAuth() {
  const auth = useClerkAuth()

  return {
    // Authentication state
    isAuthenticated: auth.isSignedIn,
    isLoading: auth.isLoaded === false,

    // User information
    userId: auth.userId,
    sessionId: auth.sessionId,

    // Auth actions (if needed)
    signOut: auth.signOut,

    // Full auth object (for advanced cases)
    auth,
  }
}
