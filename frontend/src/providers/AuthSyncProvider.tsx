import { useAuth, useUser } from "@clerk/clerk-react"
import { useEffect } from "react"
import { useAuthStore } from "@/shared/stores/authStore"
import React from "react"

export function AuthSyncProvider({ children }: { children: React.ReactNode }) {
  const auth = useAuth()
  const { user } = useUser()
  const { setAuthData, clearAuth, setIsLoaded } = useAuthStore()

  useEffect(() => {
    // Set loading state
    setIsLoaded(auth.isLoaded)

    if (!auth.isLoaded) {
      console.log("🔄 Auth not loaded yet")
      return
    }

    if (!auth.isSignedIn || !auth.userId) {
      console.log("🔒 User not signed in, clearing auth store")
      clearAuth()
      return
    }

    // Log the entire sessionClaims to debug
    console.log("🔍 Full sessionClaims:", auth.sessionClaims)
    console.log("🔍 User object:", user)

    // Try to extract role from different possible locations
    const role =
      (auth.sessionClaims as any)?.role ||  // Direct role property (backend expects this)
      (auth.sessionClaims as any)?.user_role ||  // Alternative naming
      (auth.sessionClaims as any)?.metadata?.role ||  // In metadata
      (auth.sessionClaims as any)?.public_metadata?.role ||  // In public_metadata
      user?.publicMetadata?.role as string ||  // From user public metadata
      null

    const isAppOwner =
      (auth.sessionClaims as any)?.isAppOwner ||
      (auth.sessionClaims as any)?.is_app_owner ||
      user?.publicMetadata?.isAppOwner as boolean ||
      role === "app_owner" ||
      false

    const email = user?.primaryEmailAddress?.emailAddress ||
                  user?.emailAddresses?.[0]?.emailAddress ||
                  null

    console.log("✅ Extracted role:", role)
    console.log("✅ Is app owner:", isAppOwner)
    console.log("✅ User ID:", auth.userId)
    console.log("✅ Email:", email)

    // Update the store with all auth data at once
    setAuthData({
      userId: auth.userId,
      email: email,
      role: role,
      isAppOwner: isAppOwner,
      sessionClaims: auth.sessionClaims || {},
      isSignedIn: true,
    })

  }, [
    auth.isLoaded,
    auth.isSignedIn,
    auth.sessionClaims,
    auth.userId,
    user,
    setAuthData,
    clearAuth,
    setIsLoaded
  ])

  return <>{children}</>
}
