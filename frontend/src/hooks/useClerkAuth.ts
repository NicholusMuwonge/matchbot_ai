import { useAuth, useUser } from "@clerk/clerk-react"
import { useNavigate } from "@tanstack/react-router"

const debugAuth = (action: string, data?: any) => {
  if (import.meta.env.DEV) {
    console.log(`[useClerkAuth] ${action}:`, data)
  }
}

export const useClerkAuth = () => {
  const {
    isLoaded,
    isSignedIn,
    userId,
    signOut: clerkSignOut
  } = useAuth()

  const { user } = useUser()
  const navigate = useNavigate()

  const logout = async () => {
    try {
      debugAuth("Sign out initiated")
      await clerkSignOut()
      debugAuth("Sign out successful")
      navigate({ to: "/" })
    } catch (error) {
      debugAuth("Sign out error", error)
      console.error("Sign out failed:", error)
    }
  }

  const getCurrentUser = () => {
    if (!isSignedIn || !user) {
      debugAuth("No current user - not signed in")
      return null
    }

    return {
      id: user.id,
      email: user.primaryEmailAddress?.emailAddress || "",
      firstName: user.firstName,
      lastName: user.lastName,
      imageUrl: user.imageUrl,
      fullName: user.fullName || `${user.firstName || ""} ${user.lastName || ""}`.trim(),
      isActive: true,
    }
  }

  return {
    isLoaded,
    isSignedIn,
    userId,
    user: getCurrentUser(),
    logout,
    error: null,
    resetError: () => {},
  }
}

export const isLoggedIn = () => {
  return false
}

export default useClerkAuth
