import { SignedIn, SignedOut, useAuth } from "@clerk/clerk-react"
import { useRouter } from "@tanstack/react-router"
import React from "react"

interface ClerkAuthWrapperProps {
  children: React.ReactNode
}

const debugAuth = (action: string, data?: any) => {
  if (import.meta.env.DEV) {
    console.log(`[ClerkAuthWrapper] ${action}:`, data)
  }
}

export default function ClerkAuthWrapper({ children }: ClerkAuthWrapperProps) {
  const router = useRouter()
  const auth = useAuth()

  React.useEffect(() => {
    debugAuth("Auth wrapper mounted")
  }, [])

  React.useEffect(() => {
    if (auth.isLoaded && !auth.isSignedIn) {
      debugAuth("User not signed in - redirecting to login")
      router.navigate({ to: "/login" })
    }
  }, [auth.isLoaded, auth.isSignedIn, router])

  if (!auth.isLoaded) {
    debugAuth("Auth still loading")
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        Loading authentication...
      </div>
    )
  }

  if (!auth.isSignedIn) {
    debugAuth("User not signed in - showing loading while redirecting")
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        Redirecting to login...
      </div>
    )
  }

  debugAuth("User signed in - rendering protected content")
  return <>{children}</>
}
