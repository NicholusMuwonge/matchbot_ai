import { useAuth } from "@clerk/clerk-react"
import { Navigate } from "@tanstack/react-router"
import React from "react"

interface ProtectedRouteProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

const debugProtected = (action: string, data?: any) => {
  if (import.meta.env.DEV) {
    console.log(`[ProtectedRoute] ${action}:`, data)
  }
}

export default function ProtectedRoute({
  children,
  fallback = <div>Redirecting to login...</div>,
}: ProtectedRouteProps) {
  const { isLoaded, isSignedIn, userId } = useAuth()

  React.useEffect(() => {
    debugProtected("Route protection check", {
      isLoaded,
      isSignedIn,
      userId,
    })
  }, [isLoaded, isSignedIn, userId])

  if (!isLoaded) {
    debugProtected("Auth still loading")
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
        }}
      >
        Checking authentication...
      </div>
    )
  }

  if (!isSignedIn) {
    debugProtected("User not signed in - blocking access")
    return fallback
  }

  debugProtected("User authenticated - allowing access", { userId })
  return <>{children}</>
}
