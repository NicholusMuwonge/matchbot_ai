import { useAuth, useUser } from "@clerk/clerk-react"
import { useMemo } from "react"
import type { AuthState, ClerkUser } from "../types/auth.types"

/**
 * Wrapper hook around Clerk's authentication hooks
 * Provides consistent interface compatible with existing useAuth hook
 */
export const useClerkAuth = (): AuthState & {
  logout: () => Promise<void>
} => {
  const { isSignedIn, isLoaded, signOut } = useAuth()
  const { user } = useUser()

  const mappedUser = useMemo((): ClerkUser | null => {
    if (!user) return null

    return {
      id: user.id,
      email: user.primaryEmailAddress?.emailAddress,
      full_name: user.fullName || undefined,
      first_name: user.firstName || undefined,
      last_name: user.lastName || undefined,
      profile_image_url: user.imageUrl || undefined,
      created_at: user.createdAt?.toISOString(),
      email_verified:
        user.primaryEmailAddress?.verification?.status === "verified",
    }
  }, [user])

  const logout = async (): Promise<void> => {
    await signOut()
  }

  return {
    user: mappedUser,
    isSignedIn: isSignedIn ?? false,
    isLoaded: isLoaded ?? false,
    logout,
  }
}
