import { useAuthStore } from "@/shared/stores/authStore"

/**
 * Hook to access role-based authentication data from the auth store
 * This provides a consistent interface for role checking throughout the app
 */
export function useRoleAccess() {
  const {
    userRole,
    isAppOwner: storeIsAppOwner,
    isLoaded,
    isSignedIn,
    hasRole,
    isAdmin,
    isPlatformAdmin,
  } = useAuthStore()

  // Return the auth store methods directly for better performance
  // The store already has memoized computed getters
  return {
    userRole,
    hasRole,
    isAdmin,
    isAppOwner: () => storeIsAppOwner,
    isPlatformAdmin,
    isLoaded,
    isSignedIn,
  }
}
