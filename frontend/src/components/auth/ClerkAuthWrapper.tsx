import React from "react"
import { SignedIn, SignedOut, RedirectToSignIn } from "@clerk/clerk-react"

interface ClerkAuthWrapperProps {
  children: React.ReactNode
}

const debugAuth = (action: string, data?: any) => {
  if (import.meta.env.DEV) {
    console.log(`[ClerkAuthWrapper] ${action}:`, data)
  }
}

export default function ClerkAuthWrapper({ children }: ClerkAuthWrapperProps) {
  React.useEffect(() => {
    debugAuth("Auth wrapper mounted")
  }, [])

  return (
    <>
      <SignedIn>
        {debugAuth("User signed in - rendering protected content")}
        {children}
      </SignedIn>
      <SignedOut>
        {debugAuth("User signed out - redirecting to sign in")}
        <RedirectToSignIn />
      </SignedOut>
    </>
  )
}
